#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2014-2016 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
High-level support facilities for `pkg_resources`, a mandatory runtime
dependency simplifying inspection of `betse` dependencies.
'''

# ....................{ IMPORTS                            }....................
import pkg_resources
from pkg_resources import DistributionNotFound, Requirement, VersionConflict

from betse import metadata
from betse.exceptions import BetseExceptionModule
from betse.util.io.log import logs

# ....................{ GLOBALS ~ dict                     }....................
SETUPTOOLS_TO_MODULE_NAME = {
    'Matplotlib': 'matplotlib',
    'Numpy': 'numpy',
    'Pillow': 'PIL',
    'PyYAML': 'yaml',
    'SciPy': 'numpy',
    'setuptools': 'setuptools',
    'six': 'six',
    'yamale': 'yamale',
}
'''
Dictionary mapping each relevant `setuptools`-specific project name (e.g.,
`PyYAML`) to the fully-qualified name of the corresponding top-level module or
package providing that project (e.g., `yaml`).

For consistency, the size of this dictionary should be greater than or equal to
the size of the `betse.metadata.DEPENDENCIES_RUNTIME` unordered set.
'''

# ....................{ EXCEPTIONS                         }....................
def die_unless_requirements_satisfiable_all() -> None:
    '''
    Raise an exception unless all mandatory runtime dependencies of `betse` are
    **satisfiable** (i.e., importable and of a satisfactory version).

    See Also
    ----------
    dependencies.die_unless_satisfiable_all()
        For further commentary.
    '''
    # Set of all BETSE-specific dependencies as instances of the
    # setuptools-specific "Requirements" class.
    requirements = pkg_resources.parse_requirements(
        metadata.DEPENDENCIES_RUNTIME)

    # Validate such dependencies.
    for requirement in requirements:
        die_unless_requirement_satisfiable(requirement)

def die_unless_requirement_satisfiable(requirement: Requirement) -> None:
    '''
    Raise an exception unless all mandatory runtime dependencies of `betse` are
    **satisfiable** (i.e., importable and of a satisfactory version).

    Equivalently, this function raises an exception if at least one such
    dependency is unsatisfied. For importable unsatisfied dependencies with
    `setuptools`-specific metadata (e.g., `.egg-info/`-suffixed subdirectories
    of the `site-packages/` directory for the active Python 3 interpreter,
    typically created by `setuptools` at install time), this function
    additionally validates the versions of such dependencies to satisfy `betse`
    requirements.
    '''
    assert isinstance(requirement, Requirement),\
        '"{}" not a setuptools-specific requirement.'.format(requirement)

    # Avoid circular import dependencies.
    from betse.util.py import modules, pys

    # Human-readable exception to be raised below if any.
    exception = None

    # If the active Python interpreter is frozen, it is unlikely that any
    # setuptools-installed eggs for frozen dependencies will have been
    # frozen into the current executable. Since the setuptools-based
    # dependency validation performed below assumes such eggs, an
    # alternative strategy is pursued:
    #
    # 1. Manually import each dependency.
    # 2. Compare such dependency's embedded "__version__" attribute (if
    #    any) by such dependency's required version.
    #
    # Since this strategy is inherently less reliable than setuptools-based
    # dependency validation, the latter remains the default under
    # non-frozen Python interpreters.
    # print('Validating dependency: ' + requirement.project_name)
    if pys.is_frozen():
    # if True:
        # If this requirement's setuptools-specific distribution name has *NOT*
        # been mapped to a module name, raise an exception.
        if requirement.project_name not in SETUPTOOLS_TO_MODULE_NAME:
            raise BetseExceptionModule(
                'Mandatory dependency "{}" mapped to no module name.'.format(
                    requirement))

        # Fully-qualified name of the corresponding module.
        module_name = SETUPTOOLS_TO_MODULE_NAME[requirement.project_name]

        # Such module if found or a raised exception otherwise.
        try:
            # print('Importing dependency: ' + module_name)
            module = modules.import_module(module_name)
        # Convert such exception to human-readable form.
        except ImportError:
            exception = BetseExceptionModule(
                'Mandatory dependency "{}" not found.'.format(requirement))

        # If a human-readable exception is to be raised, do so. See below.
        if exception:
            raise exception

        # Module version if any or None otherwise.
        module_version = modules.get_version_or_none(module)

        # If such version does *NOT* exist, log a non-fatal warning.
        if module_version is None:
            logs.log_info(
                'Mandatory dependency "%s" version not found.', module_name)
        # Else if such version does *NOT* satisfy the current requirement, raise
        # an exception.
        elif module_version not in requirement:
            raise BetseExceptionModule(
                'Mandatory dependency "{}" unsatisfied by installed version {}.'.format(
                str(requirement), module_version))
    # Else, the active Python interpreter is *NOT* frozen. As discussed,
    # prefer setuptools-based dependency validation.
    else:
        # If setuptools raises a non-human-readable exception on attempting
        # to validate such dependency, convert that to a human-readable
        # exception.
        try:
            pkg_resources.get_distribution(requirement)
        # If such dependency does *NOT* exist, a non-human-readable
        # resembling the following is raised:
        #
        #    pkg_resources.DistributionNotFound: PyYAML>=3.10
        except DistributionNotFound:
            exception = BetseExceptionModule(
                'Mandatory dependency "{}" not found.'.format(requirement))
        # If such dependency exists but is of an insufficient version, a
        # non-human-readable resembling the following is raised:
        #
        #    pkg_resources.VersionConflict: (PyYAML 3.09 (/usr/lib64/python3.3/site-packages), Requirement.parse('PyYAML>=3.10'))
        except VersionConflict as version_conflict:
            exception = BetseExceptionModule(
                'Mandatory dependency "{}" unsatisfied by installed dependency "{}".'.format(
                    version_conflict.req, version_conflict.dist))

        # If a human-readable exception is to be raised, do so. While it
        # would be preferable to simply raise such exception in the above
        # exception handler, doing so induces Python 3 to implicitly
        # prepend such exception by the non-human-readable exception
        # setuptools raised above. Which is what we *DON'T* want to happen.
        if exception:
            raise exception

# --------------------( WASTELANDS                         )--------------------
# ....................{ GLOBALS                            }....................
# DISTRIBUTION_TO_MODULE_NAME = {
#     'Matplotlib': 'matplotlib',
#     'Numpy': 'numpy',
#     'SciPy': 'numpy',
#     'PyYAML': 'yaml',
# }
# '''
# Dictionary mapping from setuptools-specific distribution names (e.g., `PyYAML`)
# to standard fully-qualified module names (e.g., `yaml`).
# '''

        # # Fully-qualified name of the corresponding module. If this
        # # requirement's setuptools-specific distribution name maps to an actual
        # # module name, prefer the latter; else, fallback to the former.
        # module_name = DISTRIBUTION_TO_MODULE_NAME.get(
        #     requirement.project_name, requirement.project_name)
