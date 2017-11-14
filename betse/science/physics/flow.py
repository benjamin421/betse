#!/usr/bin/env python3
# Copyright 2014-2017 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

import numpy as np
from betse.science import sim_toolbox as stb
from scipy.ndimage.filters import gaussian_filter
from betse.science.math import finitediff as fd


def getFlow(sim, cells, p):
    """
    Calculate the electroosmotic fluid flow in the cell and extracellular
    networks using Stokes-Equation

    """

    # First do extracellular space electroosmotic flow--------------------------------------------------------------

    if p.is_ecm is True:


        # # scaleF = (p.cell_space / cells.delta)
        # scaleF = 1.0
        #
        # # rho_env = fd.integrator(sim.rho_env.reshape(cells.X.shape))
        # rho_env = sim.rho_env.reshape(cells.X.shape)
        #
        # muFx = (1 / p.mu_water)*sim.E_env_x*rho_env*scaleF*sim.D_env_weight
        # muFy = (1 / p.mu_water)*sim.E_env_y*rho_env*scaleF*sim.D_env_weight
        #
        # uxo = np.dot(cells.lapENVinv, -muFx.ravel())
        # uyo = np.dot(cells.lapENVinv, -muFy.ravel())
        #
        # _, sim.u_env_x, sim.u_env_y, _, _, _ = stb.HH_Decomp(uxo, uyo, cells)

        #--Alternative method #1 calculates fluid flow in terms of slip velocity only:----------------------------------

        scaleF =  (sim.ko_env*p.cell_height) # conversion concentrating charge density in the double layer

        # total charge in an env-grid square in Coulombs:
        q_env = sim.rho_env.reshape(cells.X.shape)*(cells.delta**2)*(p.cell_height)

        # slip velocity forces:
        muFx = (1/p.mu_water)*sim.E_env_x*q_env*scaleF*sim.D_env_weight
        muFy = (1/p.mu_water)*sim.E_env_y*q_env*scaleF*sim.D_env_weight


        _, sim.u_env_x, sim.u_env_y, _, _, _ = stb.HH_Decomp(muFx, muFy, cells)


        # Alternative method #2 calculates flow in terms of curl component of current density:--------------------------
        # cc = sim.cc_env.mean(axis=0).reshape(cells.X.shape)
        # zz = sim.zs.mean()
        #
        # sim.u_env_x = -sim.J_env_x / (p.F * cc * zz)
        # sim.u_env_y = -sim.J_env_y / (p.F * cc * zz)



    # -------Next do flow through gap junction connected cells-------------------------------------------------------

    # Charge density per unit volume:
    rho_cells = np.dot(sim.zs * p.F, sim.cc_cells) + sim.extra_rho_cells

    # net force is the electrostatic body force on net volume charge in cells:
    Fxc = sim.E_cell_x*rho_cells*(1/p.mu_water)
    Fyc = sim.E_cell_y*rho_cells*(1/p.mu_water)

    # Calculate flow under body forces using Stokes flow:
    u_gj_xo = np.dot(cells.lapGJinv, -Fxc)
    u_gj_yo = np.dot(cells.lapGJinv, -Fyc)

    # Flow must be made divergence-free: use the Helmholtz-Hodge decomposition method:
    _, sim.u_cells_x, sim.u_cells_y, _, _, _ = cells.HH_cells(u_gj_xo, u_gj_yo, rot_only=True)

