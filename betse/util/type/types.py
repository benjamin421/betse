#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2014-2015 by Alexis Pietak & Cecil Curry
# See "LICENSE" for further details.

'''
Low-level **type testers** (i.e., functions testing the types of passed
objects).
'''
# ....................{ IMPORTS                            }....................
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# WARNING: To avoid non-halting recursive imports when imported at the top-level
# of other modules in the `betse.util` package, this module may import *ONLY*
# from stock Python packages. (By definition, this excludes all BETSE packages.)
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

# ....................{ IMPORTS                            }....................
from collections.abc import Iterable, Mapping, Sequence

# ....................{ TESTERS                            }....................
def is_bool(obj: object) -> bool:
    '''
    `True` if the passed object is **boolean** (i.e., either `True` or `False`).
    '''
    return isinstance(obj, bool)


def is_char(obj: object) -> bool:
    '''
    `True` if the passed object is a **character** (i.e., a string of length 1).
    '''
    return is_str(obj) and len(obj) == 1


def is_mapping(obj: object) -> bool:
    '''
    `True` if the passed object is a **mapping** (i.e., indexable by strings).

    The canonical examples are `dict` and `OrderedDict` instances.
    '''
    return isinstance(obj, Mapping)

# ....................{ TESTERS ~ iterable                 }....................
def is_iterable(obj: object) -> bool:
    '''
    `True` if the passed object is an **iterable**.

    Iterables are objects capable of returning their members one at a time.
    Equivalently, iterables implement the abstract base class
    `collections.Iterable` and hence define the `__iter__()` method.
    '''
    return isinstance(obj, Iterable)


def is_iterable_nonstr(obj: object) -> bool:
    '''
    `True` if the passed object is a **non-string iterable** (i.e., implements
    the abstract base class `collections.Iterable` _and_ is not a string).
    '''
    return is_iterable(obj) and not is_str(obj)

# ....................{ TESTERS ~ numeric                  }....................
def is_int(obj: object) -> bool:
    '''
    `True` if the passed object is an integer.
    '''
    return isinstance(obj, int)


def is_int_ge(obj: object, ge: int) -> bool:
    '''
    `True` if the passed object is an integer greater than or equal to the
    second passed integer.
    '''
    assert is_int(ge), assert_not_int(ge)
    return is_int(obj) and obj >= ge


def is_numeric(obj: object) -> bool:
    '''
    `True` if the passed object is **numeric** (i.e., instance of either the
    `int` or `float` classes).
    '''
    return isinstance(obj, (int, float))

# ....................{ TESTERS ~ sequence                 }....................
def is_sequence(obj: object) -> bool:
    '''
    `True` if the passed object is a **sequence**.

    Sequences are iterables supporting efficient element access via integer
    indices. Equivalently, sequences implement the abstract base class
    `collections.Sequence` and hence define the `__getitem__()` and `__len__()`
    methods (among numerous others).

    While all sequences are iterables, not all iterables are sequences.
    Generally speaking, sequences correspond to the proper subset of iterables
    whose elements are ordered. `dict` and `OrderedDict` are the canonical
    examples. `dict` implements `collections.Iterable` but _not_
    `collections.Sequence`, due to _not_ supporting integer index-based lookup;
    `OrderedDict` implements both, due to supporting such lookup.
    '''
    return isinstance(obj, Sequence)


def is_sequence_nonstr(obj: object) -> bool:
    '''
    `True` if the passed object is a **non-string sequence** (i.e., implements
    the abstract base class `collections.Sequence` _and_ is not a string).
    '''
    return is_sequence(obj) and not is_str(obj)


def is_sequence_nonstr_nonempty(obj: object) -> bool:
    '''
    `True` if the passed object is a **nonempty non-string sequence** (i.e.,
    implements the abstract base class `collections.Sequence`, is not a string,
    and contains at least one element).
    '''
    return is_sequence_nonstr(obj) and len(obj)

# ....................{ TESTERS ~ science                  }....................
def is_cells(obj: object) -> bool:
    '''
    `True` if the passed object is an instance of the BETSE-specific `Cells`
    class.
    '''
    # Avoid circular import dependencies.
    from betse.science.cells import Cells
    return isinstance(obj, Cells)

def is_parameters(obj: object) -> bool:
    '''
    `True` if the passed object is an instance of the BETSE-specific
    `Parameters` class.
    '''
    # Avoid circular import dependencies.
    from betse.science.parameters import Parameters
    return isinstance(obj, Parameters)

def is_simulator(obj: object) -> bool:
    '''
    `True` if the passed object is an instance of the BETSE-specific `Simulator`
    class.
    '''
    # Avoid circular import dependencies.
    from betse.science.sim import Simulator
    return isinstance(obj, Simulator)

def is_tissue_picker(obj: object) -> bool:
    '''
    `True` if the passed object is an instance of the BETSE-specific
    `TissuePicker` class.
    '''
    # Avoid circular import dependencies.
    from betse.science.tissue.picker import TissuePicker
    return isinstance(obj, TissuePicker)

# ....................{ TESTERS ~ str                      }....................
def is_str(obj: object) -> bool:
    '''
    `True` if the passed object is a **string** (i.e., instance of the `str`
    class).
    '''
    return isinstance(obj, str)


def is_str_nonempty(obj: object) -> bool:
    '''
    `True` if the passed object is a **nonempty string* (i.e., string comprising
    one or more characters and hence _not_ the empty string).
    '''
    return is_str(obj) and len(obj)

# ....................{ ASSERTERS                          }....................
def assert_not_bool(obj: object) -> str:
    '''
    String asserting the passed object to _not_ be boolean.
    '''
    return '"{}" not boolean (i.e., neither "True" nor "False").'.format(obj)


def assert_not_char(obj: object) -> str:
    '''
    String asserting the passed object to _not_ be character.
    '''
    return '"{}" not a character (i.e., string of length 1).'.format(obj)


def assert_not_mapping(obj: object) -> str:
    '''
    String asserting the passed object to _not_ be a mapping.
    '''
    return '"{}" not a mapping (e.g., "dict", "OrderedDict").'.format(obj)

# ....................{ ASSERTERS ~ iterable               }....................
def assert_not_iterable_nonstr(obj: object) -> str:
    '''
    String asserting the passed object to _not_ be a non-string iterable.
    '''
    return '"{}" not a non-string iterable (e.g., dict, list).'.format(obj)


def assert_not_iterable_nonstr_nonempty(obj: object, label: str) -> str:
    '''
    String asserting the passed object categorized by the passed human-readable
    label to _not_ be a nonempty non-string iterable.
    '''
    return assert_not_iterable_nonstr(obj) if not is_iterable_nonstr(
        obj) else '{} empty.'.format(label.capitalize())

# ....................{ ASSERTERS ~ numeric                }....................
def assert_not_int(obj: object) -> str:
    '''
    String asserting the passed object to _not_ be an integer.
    '''
    return '"{}" not an integer.'.format(obj)


def assert_not_int_ge(obj: object, ge: int) -> str:
    '''
    String asserting the passed object to _not_ be an integer greater than or
    equal to the second passed integer.
    '''
    return '"{}" not an integer or not >= {}.'.format(obj, ge)


def assert_not_numeric(obj: object) -> str:
    '''
    String asserting the passed object to _not_ be numeric.
    '''
    return '"{}" not numeric (i.e., neither an integer nor float).'.format(obj)

# ....................{ ASSERTERS ~ sequence               }....................
def assert_not_sequence_nonstr(obj: object) -> str:
    '''
    String asserting the passed object to _not_ be a non-string sequence.
    '''
    return '"{}" not a non-string sequence (e.g., list).'.format(obj)

def assert_not_sequence_nonstr_nonempty(obj: object, label: str) -> str:
    '''
    String asserting the passed object categorized by the passed human-readable
    label to _not_ be a nonempty non-string sequence.
    '''
    return assert_not_sequence_nonstr(obj) if not is_sequence_nonstr(
        obj) else '{} empty.'.format(label.capitalize())

# ....................{ ASSERTERS ~ science                }....................
def assert_not_cells(obj: object) -> str:
    '''
    String asserting the passed object to _not_ be an instance of the BETSE-
    specific `Cells` class.
    '''
    return '"{}" not a "Cells" instance.'.format(obj)

def assert_not_parameters(obj: object) -> str:
    '''
    String asserting the passed object to _not_ be an instance of the BETSE-
    specific `Parameters` class.
    '''
    return '"{}" not a "Parameters" instance.'.format(obj)

def assert_not_simulator(obj: object) -> str:
    '''
    String asserting the passed object to _not_ be an instance of the BETSE-
    specific `Simulator` class.
    '''
    return '"{}" not a "Simulator" instance.'.format(obj)

def assert_not_tissue_picker(obj: object) -> str:
    '''
    String asserting the passed object to _not_ be an instance of the BETSE-
    specific `TissuePicker` class.
    '''
    return '"{}" not a "TissuePicker" instance.'.format(obj)

# ....................{ ASSERTERS ~ str                    }....................
def assert_not_str(obj: object) -> str:
    '''
    String asserting the passed object to _not_ be a string.
    '''
    return '"{}" not a string.'.format(obj)

def assert_not_str_nonempty(obj: object, label: str) -> str:
    '''
    String asserting the passed object categorized by the passed human-readable
    label to _not_ be a nonempty string.
    '''
    return assert_not_str(obj) if not is_str(obj) else\
        '{} empty.'.format(label.capitalize())
