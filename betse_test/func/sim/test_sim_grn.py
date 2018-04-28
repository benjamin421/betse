#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2014-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
CLI-specific functional tests exercising all simulation subcommands pertaining
to gene regulatory networks (e.g., `betse sim-grn`, `betse plot sim-grn`).
'''

# ....................{ IMPORTS                            }....................
from betse_test.util.mark.skip import skip_unless_lib_runtime_optional

# ....................{ DECORATORS                         }....................
skip_unless_networkable = skip_unless_lib_runtime_optional('networkx', 'pydot')
'''
Decorator skipping the decorated test if either of these optional runtime
dependencies are unavailable, both of which are required by network plotting
subcommands (e.g., ``plot sim-grn``).
'''

# ....................{ TESTS                              }....................
#FIXME: Parametrize this test with all members of the "GrnUnpicklePhaseType"
#enumeration. See the "test_sim" submodule for similar logic: e.g.,
# @skip_unless_networkable
# @pytest.mark.parametrize(
#     ('writer_name', 'filetype'), (
#         skip_unless_matplotlib_anim_writer('avconv')(('avconv', 'mp4',))))
def test_cli_grn_isolated(betse_cli_sim: 'CLISimTester') -> None:
    '''
    Test simulating the default gene regulatory network (GRN) isolated away from
    all bioelectrical phenomena.

    Parameters
    ----------
    betse_cli_sim : CLISimTester
        Object running BETSE CLI simulation subcommands.
    '''

    # Defer heavyweight imports.
    from betse.science.config.confenum import GrnUnpicklePhaseType
    from betse.util.io.log import logs
    from betse.util.path import pathnames

    # Simulation configuration specific to this test.
    p = betse_cli_sim.sim_state.p

    #FIXME: Replace this overkill method call with direct usage of the local
    #"p" parameter; then remove this method entirely from the codebase.
    # Enable these networks.
    betse_cli_sim.sim_state.config.enable_networks()

    # Ensure that the
    p.grn_unpickle_phase_type = GrnUnpicklePhaseType.SEED

    # Enable the saving of visuals, preventing the "plot sim-grn" subcommand
    # tested below from silently reducing to a noop.
    betse_cli_sim.sim_state.config.enable_visuals_save()

    # Test all GRN-specific subcommands required to simulate from scratch with
    # this configuration.
    betse_cli_sim.run_subcommands(('seed',), ('sim-grn',),)

    # Log this rerun attempt with suitable aesthetics.
    logs.log_banner(title='sim-grn (rerun)', padding='~')

    # Prepare to rerun the "sim-grn" subcommand from the prior run pickled by
    # the prior subcommand. To do so safely (in order):
    #
    # * Reconstruct the relative filename of the prior GRN run.
    # * Ensure that the next GRN run is pickled to another file.
    p.grn_unpickle_filename_relative = pathnames.join(
        p.grn_pickle_dirname_relative, p.grn_pickle_basename)
    p.grn_pickle_basename = 'new_' + p.grn_pickle_basename

    # Redefine all absolute pathnames depending upon these relative pathnames.
    p.reload_paths()

    # Test rerunning the "sim-grn" subcommand from the prior such run and, for
    # completeness, exporting the results of doing so.
    betse_cli_sim.run_subcommands(('sim-grn',), ('plot', 'sim-grn',),)


@skip_unless_networkable
def test_cli_sim_grn_integrated(betse_cli_sim: 'CLISimTester') -> None:
    '''
    Test simulating the default gene regulatory network (GRN) integrated
    together with all bioelectrical phenomena.

    Parameters
    ----------
    betse_cli_sim : CLISimTester
        Object running BETSE CLI simulation subcommands.
    '''

    # Enable these networks.
    betse_cli_sim.sim_state.config.enable_networks()

    # Test all default simulation-specific subcommands with this configuration.
    betse_cli_sim.run_subcommands_try()
