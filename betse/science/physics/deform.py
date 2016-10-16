
#!/usr/bin/env python3
# Copyright 2014-2016 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

import numpy as np
from scipy import interpolate as interp
from scipy.ndimage.filters import gaussian_filter
from betse.exceptions import BetseSimulationException
from betse.science import sim_toolbox as stb
from betse.util.io.log import logs
from scipy.interpolate import SmoothBivariateSpline
from scipy.sparse.linalg import lsmr


# FIXME!!! change over to HH decomposition!


def getDeformation(sim, cells, t, p):
    """
    Calculates the deformation of the cell cluster under the action
    of intracellular forces and pressures, assuming steady-state
    (slow) changes.

    The method assumes that material is incompressible and total volume is conserved.

    If studying galvanotropism, cells are assumed to move directly under the influence
    of the global electric field generated by net ion currents in the tissue cluster.

    If studying hydrostatic pressure deformations under osmotic influx, first,
    the equation of linear elastic motion is used to calculate
    deformation assuming full compressibility.

    The divergence of the resulting deformation field is calculated,
    an internal reaction pressure is calculated from the divergence.
    The gradient of the reaction pressure is subtracted from the initial
    solution to create a divergence-free (volume conserved) deformation field.

    """

    # Determine action forces
    #---------------------------------------------------------------------------------

    # deformation by galvanotropism:

    if p.sim_ECM is True:

        ux_galvo_mem = (1 / p.lame_mu) * p.media_sigma * sim.J_env_x.ravel()[cells.map_mem2ecm] * p.galvanotropism
        uy_galvo_mem = (1 / p.lame_mu) * p.media_sigma * sim.J_env_y.ravel()[cells.map_mem2ecm] * p.galvanotropism

    else:

        ux_galvo_mem = (1 / p.lame_mu) * p.media_sigma * sim.J_mem_x * p.galvanotropism
        uy_galvo_mem = (1 / p.lame_mu) * p.media_sigma * sim.J_mem_y * p.galvanotropism

    if p.deform_osmo is True:

        # u_osmo is negative as it's defined + into the cell in pressures.py
        u_osmo = -sim.u_net

    else:
        u_osmo = np.zeros(sim.mdl)


    # --calculate displacement field for incompressible medium------------------------------------------------

    # calculate the initial displacement field (not divergence free!) for the forces using the linear elasticity
    # equation:

    # if p.fixed_cluster_bound is True:
    #
    #     u_x_o = np.dot(cells.lapGJinv, -(1 / p.lame_mu) * (F_cell_x))  # FIXME solve with lapGJ_P and lsmr
    #     u_y_o = np.dot(cells.lapGJinv, -(1 / p.lame_mu) * (F_cell_y))  # FIXME solve with lapGJ_P and lsmr
    #
    #     # enforce boundary conditions on u:
    #     if p.fixed_cluster_bound is True:
    #         u_x_o[cells.bflags_cells] = 0
    #         u_y_o[cells.bflags_cells] = 0
    #         u_x_o[cells.nn_bound] = 0
    #         u_y_o[cells.nn_bound] = 0
    #
    # else:
    #
    #     u_x_o = np.dot(cells.lapGJ_P_inv, -(1 / p.lame_mu) * (F_cell_x))
    #     u_y_o = np.dot(cells.lapGJ_P_inv, -(1 / p.lame_mu) * (F_cell_y))


    # get the normal component of the deformation at the membranes:
    u_n = ux_galvo_mem * cells.mem_vects_flat[:, 2] + uy_galvo_mem * cells.mem_vects_flat[:, 3]

    # calculate divergence as the sum of this vector times each surface area, divided by cell volume:
    div_u = (np.dot(cells.M_sum_mems, u_n * cells.mem_sa) / cells.cell_vol) - sim.div_u_osmo

    # calculate the reaction pressure required to counter-balance the deform field field:
    if p.fixed_cluster_bound is True:

        P_react = np.dot(cells.lapGJ_P_inv, div_u)
        # P_react = lsmr(cells.lapGJ_P, div_u)[0]

    else:

        P_react = np.dot(cells.lapGJinv, div_u)
        # P_react = lsmr(cells.lapGJ, div_u)[0]

    # calculate its gradient:
    gradP_react = (P_react[cells.cell_nn_i[:, 1]] - P_react[cells.cell_nn_i[:, 0]]) / (cells.nn_len)

    # correct the deformation:
    u_net = u_n - gradP_react

    ux = u_net*cells.mem_vects_flat[:,2]
    uy = u_net*cells.mem_vects_flat[:,3]

    # calculate the net displacement of cell centres under the applied force under incompressible conditions:
    sim.d_cells_x = np.dot(cells.M_sum_mems, ux) / cells.num_mems
    sim.d_cells_y = np.dot(cells.M_sum_mems, uy) / cells.num_mems

    # enforce boundary conditions:
    if p.fixed_cluster_bound is True:
        sim.d_cells_x[cells.bflags_cells] = 0
        sim.d_cells_y[cells.bflags_cells] = 0

def timeDeform(sim, cells, t, p):
    """
    Calculates the deformation of the cell cluster under the action
    of intracellular pressure, considering the full time-dependent
    linear elasticity equation for an incompressible medium.

    The solution method for this equation is similar to the
    steady-state method of deformation(). First the displacement
    field is calculated assuming compressibility,
    a reaction pressure is calculated from the divergence of the
    initial field, and the gradient of the internal pressure is
    subtracted from the initial field to produce a divergence
    free solution.

    This method is working much better than the timeDeform_o()
    so is presently in active use.

    """

    # Check for the adequacy of the time step:
    step_check = (p.dt / (2 * p.rc)) * np.sqrt(p.lame_mu / 1000)

    if step_check > 1.0:
        new_ts = (0.9 * 2 * p.rc) / (np.sqrt(p.lame_mu / 1000))

        raise BetseSimulationException(
            'Time dependent deformation is tricky business, requiring a small time step! '
            'The time step you are using is too large to bother going further with. '
            'Please set your time step to ' + str(new_ts) + ' and try again.')

    k_const = (p.dt ** 2) * (p.lame_mu / 1000)

    # # Determine action forces ------------------------------------------------

    # body force from hydrostatic pressure:
    F_hydro_x = sim.F_hydro_x
    F_hydro_y = sim.F_hydro_y

    # first determine body force components due to electrostatics, if desired:
    # if p.sim_ECM is True:
    #     F_electro_x =  p.media_sigma * sim.J_env_x.ravel()[cells.map_mem2ecm] * sim.rho_env.ravel()[cells.map_mem2ecm]
    #     F_electro_y =  p.media_sigma * sim.J_env_x.ravel()[cells.map_mem2ecm] * sim.rho_env.ravel()[cells.map_mem2ecm]
    #
    # else:
    #
    #     F_electro_x =  p.media_sigma * sim.J_mem_x * sim.rho_cells
    #     F_electro_y =  p.media_sigma * sim.J_mem_y * sim.rho_cells
    #
    # # map to cell centers:
    # F_electro_x = np.dot(cells.M_sum_mems, F_electro_x) / cells.num_mems
    # F_electro_y = np.dot(cells.M_sum_mems, F_electro_y) / cells.num_mems

    # Take the total component of pressure from all contributions:
    F_cell_x = F_hydro_x
    F_cell_y = F_hydro_y

    # -------------------------------------------------------------------------------------------------

    sim.dx_time.append(sim.d_cells_x[:])  # append the solution to the time-save vector
    sim.dy_time.append(sim.d_cells_y[:])

    # Initial value solution--------------------------------------------------------------------------------
    if t == 0.0:

        wave_speed = np.sqrt(p.lame_mu / 1000)
        wave_speed = np.float(wave_speed)
        wave_speed = np.round(wave_speed, 2)

        logs.log_info(
            'Your wave speed is approximately: ' +
            str(wave_speed) + ' m/s '
        )

        logs.log_info('Try a world size of at least: ' + str(round((5 / 3) * (wave_speed / 500) * 1e6))
                      + ' um for resonance.')

        if p.fixed_cluster_bound is True:

            sim.d_cells_x = k_const * np.dot(cells.lapGJ, sim.dx_time[-1]) + (k_const / p.lame_mu) * F_cell_x + \
                            sim.dx_time[-1]
            sim.d_cells_y = k_const * np.dot(cells.lapGJ, sim.dy_time[-1]) + (k_const / p.lame_mu) * F_cell_y + \
                            sim.dy_time[-1]

        else:

            sim.d_cells_x = k_const * np.dot(cells.lapGJ_P, sim.dx_time[-1]) + (k_const / p.lame_mu) * F_cell_x + \
                            sim.dx_time[-1]
            sim.d_cells_y = k_const * np.dot(cells.lapGJ_P, sim.dy_time[-1]) + (k_const / p.lame_mu) * F_cell_y + \
                            sim.dy_time[-1]


    elif t > 0.0:

        # do the non-initial value, standard solution iteration:

        # calculate the velocity for viscous damping:
        d_ux_dt = (sim.dx_time[-1] - sim.dx_time[-2]) / (p.dt)
        d_uy_dt = (sim.dy_time[-1] - sim.dy_time[-2]) / (p.dt)

        gamma = ((p.dt ** 2) * (p.mu_tissue * p.lame_mu)) / (1000 * (2 * p.rc))

        if p.fixed_cluster_bound is True:

            sim.d_cells_x = k_const * np.dot(cells.lapGJ, sim.dx_time[-1]) - gamma * d_ux_dt + \
                             (k_const / p.lame_mu) * F_cell_x + 2 * sim.dx_time[-1] - sim.dx_time[-2]

            sim.d_cells_y = k_const * np.dot(cells.lapGJ, sim.dy_time[-1]) - gamma * d_uy_dt + \
                             (k_const / p.lame_mu) * F_cell_y + 2 * sim.dy_time[-1] - sim.dy_time[-2]

        else:

            sim.d_cells_x = k_const * np.dot(cells.lapGJ_P, sim.dx_time[-1]) - gamma * d_ux_dt + \
                             (k_const / p.lame_mu) * F_cell_x + 2 * sim.dx_time[-1] - sim.dx_time[-2]

            sim.d_cells_y = k_const * np.dot(cells.lapGJ_P, sim.dy_time[-1]) - gamma * d_uy_dt + \
                             (k_const / p.lame_mu) * F_cell_y + 2 * sim.dy_time[-1] - sim.dy_time[-2]


    # calculate divergence of u  -----------------------------------------------------------------------

    # first interpolate displacement field at membrane midpoints:
    ux_mem = interp.griddata((cells.cell_centres[:, 0], cells.cell_centres[:, 1]), sim.d_cells_x,
        (cells.mem_mids_flat[:, 0], cells.mem_mids_flat[:, 1]), fill_value=0)

    uy_mem = interp.griddata((cells.cell_centres[:, 0], cells.cell_centres[:, 1]), sim.d_cells_y,
        (cells.mem_mids_flat[:, 0], cells.mem_mids_flat[:, 1]), fill_value=0)

    # get the component of the displacement field normal to the membranes:
    u_n = ux_mem * cells.mem_vects_flat[:, 2] + uy_mem * cells.mem_vects_flat[:, 3]

    # calculate divergence as the sum of this vector x each surface area, divided by cell volume:
    div_u = (np.dot(cells.M_sum_mems, u_n * cells.mem_sa) / cells.cell_vol)

    if p.fixed_cluster_bound is True:

        # calculate the reaction pressure required to counter-balance the flow field:
        P_react = np.dot(cells.lapGJ_P_inv, div_u)

    else:

        # calculate the reaction pressure required to counter-balance the flow field:
        P_react = np.dot(cells.lapGJinv, div_u)

    # calculate its gradient:
    gradP_react = (P_react[cells.cell_nn_i[:, 1]] - P_react[cells.cell_nn_i[:, 0]]) / (cells.nn_len)

    gP_x = gradP_react * cells.mem_vects_flat[:,2]
    gP_y = gradP_react * cells.mem_vects_flat[:,3]

    # average the components of the reaction force field at cell centres and get boundary values:
    gPx_cell = np.dot(cells.M_sum_mems, gP_x) / cells.num_mems
    gPy_cell = np.dot(cells.M_sum_mems, gP_y) / cells.num_mems

    # calculate the displacement of cell centres under the applied force under incompressible conditions:
    sim.d_cells_x = sim.d_cells_x - gPx_cell
    sim.d_cells_y = sim.d_cells_y - gPy_cell


    if p.fixed_cluster_bound is True:  # enforce zero displacement boundary condition:

        sim.d_cells_x[cells.bflags_cells] = 0
        sim.d_cells_y[cells.bflags_cells] = 0

        # sim.d_cells_x[cells.nn_bound] = 0
        # sim.d_cells_y[cells.nn_bound] = 0

    else: # create a single fixed point on the boundary to prevent it from floating away

        sim.d_cells_x[cells.bflags_cells[0]] = 0
        sim.d_cells_y[cells.bflags_cells[0]] = 0


    # check the displacement for NANs:
    stb.check_v(sim.d_cells_x)

def implement_deform_timestep(sim, cells, t, p):
    """
    Implements the deformation of the tissue cluster based on divergence-free deformation
    calculated for cell centres.

    """
    # create a smooth bivariate spline to interpolate deformation data from cells:
    cellinterp_x = SmoothBivariateSpline(cells.cell_centres[:, 0], cells.cell_centres[:, 1], sim.d_cells_x, kx=3, ky=3)
    cellinterp_y = SmoothBivariateSpline(cells.cell_centres[:, 0], cells.cell_centres[:, 1], sim.d_cells_y, kx=3, ky=3)

    # calculate deformations wrt the ecm using the smooth bivariate spline:
    decm_x = cellinterp_x.ev(cells.ecm_verts_unique[:, 0], cells.ecm_verts_unique[:, 1])
    decm_y = cellinterp_y.ev(cells.ecm_verts_unique[:, 0], cells.ecm_verts_unique[:, 1])

    # get the new ecm verts by applying the deformation:
    ecm_x2 = cells.ecm_verts_unique[:, 0] + decm_x
    ecm_y2 = cells.ecm_verts_unique[:, 1] + decm_y

    ecm_new = np.column_stack((ecm_x2, ecm_y2))

    # repackage new ecm vertices as cells.ecm_verts:
    ecm_verts2 = []

    for inds in cells.inds2ecmVerts:
        ecm_verts2.append(ecm_new[inds])

    # cells.ecm_verts = np.asarray(ecm_verts2)

    # rebuild essential portions of the cell world:
    cells.deformWorld(p, ecm_verts2)

    # write data to time-storage vectors:
    sim.cell_centres_time.append(cells.cell_centres[:])
    sim.mem_mids_time.append(cells.mem_mids_flat[:])
    # sim.maskM_time.append(cells.maskM[:])
    sim.mem_edges_time.append(cells.mem_edges_flat[:])
    sim.cell_verts_time.append(cells.cell_verts[:])

