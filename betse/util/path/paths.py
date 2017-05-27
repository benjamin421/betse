#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2014-2017 by Alexis Pietak & Cecil Curry
# See "LICENSE" for further details.

'''
Low-level path facilities general to all path types -- namely, both directories
and non-directory files.
'''

# ....................{ IMPORTS                            }....................
import os, shutil
from betse.exceptions import BetsePathException
from betse.util.io.log import logs
from betse.util.type.types import type_check, NumericTypes
from os import path

# ....................{ EXCEPTIONS ~ path                  }....................
def die_if_path(*pathnames: str) -> None:
    '''
    Raise an exception if any of the paths with the passed pathnames exist.

    Parameters
    ----------
    pathnames : tuple[pathnames]
        Tuple of all pathnames to be tested.

    Raises
    ----------
    BetsePathException
        If any such path exists.
    '''

    for pathname in pathnames:
        if is_path(pathname):
            raise BetsePathException(
                'Path "{}" already exists.'.format(pathname))


def die_unless_path(*pathnames: str) -> None:
    '''
    Raise an exception unless all paths with the passed pathnames exist.

    Parameters
    ----------
    pathnames : tuple[pathnames]
        Tuple of all pathnames to be tested.

    Raises
    ----------
    BetsePathException
        If any such path does *not* exist.
    '''

    for pathname in pathnames:
        if not is_path(pathname):
            raise BetsePathException(
                'Path "{}" not found or unreadable.'.format(pathname))

# ....................{ TESTERS                            }....................
@type_check
def is_path(pathname: str) -> bool:
    '''
    ``True`` only if the passed path exists *without* following this path if
    this path is an existing symbolic link.

    If this path is an existing **dangling symbolic link** (i.e., symbolic link
    whose target no longer exists, also commonly referred to as a broken
    symbolic link), this function still returns ``True``.
    '''

    # Call path.lexists() rather than path.exists(), as the latter returns False
    # for dangling symbolic links -- which is entirely irrelevant for most
    # contexts. Under POSIX semantics, dangling symbolic links are essential to
    # common usage patterns and should *NOT* be discriminated against here.
    return os.path.lexists(pathname)

# ....................{ GETTERS                            }....................
@type_check
def get_type_label(pathname: str) -> str:
    '''
    Lowercase human-readable label describing the type of the passed existing
    path.

    For brevity, this label comprises one lowercase noun optionally preceded by
    a lowercase adjective unambiguously identifying this path's type:

    * ``symbolic link`` for an existing symbolic link, regardless of whether
      that link is **dangling** (i.e., refers to a non-existent path) or not.
    * ``directory`` for an existing directory.
    * ``special file`` for all other **special files** (e.g., device node, named
      pipe, socket).
    * ``file`` for an existing regular (i.e., non-special) file).

    If this path does *not* exist, an exception is raised.
    '''

    # Avoid circular import dependencies.
    from betse.util.paths import dirs, files

    # Raise an exception unless this path exists.
    die_unless_path(pathname)

    # Get this type.
    if files.is_file(pathname):
        if files.is_symlink(pathname):
            return 'symbolic link'
        elif files.is_special(pathname):
            return 'special file'
        else:
            return 'file'
    elif dirs.is_dir(pathname):
        return 'directory'

    # Else, this existing path is neither a file or directory and is hence a
    # shambling thing that should not be. Panic. Space-time continuity itself is
    # now in question.
    raise BetsePathException(
        'Path "{}" type unrecognized.'.format(pathname))

# ....................{ GETTERS ~ time                     }....................
@type_check
def get_mtime(pathname: str) -> NumericTypes:
    '''
    Mtime (i.e., modification time) in seconds of the passed path.

    If this path is:

    * A directory, this is the most recent time at which the non-recursive
      contents of this directory were created, modified, or deleted. Since this
      function operates non-recursively, this considers *only* this directory
      itself and all immediate subdirectories and files in this directory.
    * A file, this is the most recent time at which the contents of this file
      were created or modified.
    * A symbolic link, this is the most recent time at which this symbolic link
      was created. Hence, this function does *not* follow symbolic links.

    This time does *not* consider the most recent time at which the metadata
    (e.g., permissions) of this path was created or modified, which the
    :func:`get_ctime` function provides.

    Parameters
    -----------
    pathname : str
        Relative or absolute path to inspect.

    Returns
    -----------
    NumericTypes
        Mtime in seconds of this path as either an integer or float, depending
        on the boolean returned by the platform-specific
        :func:`os.stat_float_times` function.
    '''

    return path.getmtime(pathname)


@type_check
def get_mtime_newest(*pathnames: str) -> NumericTypes:
    '''
    Mtime (i.e., modification time) in seconds of the most recent passed path.

    For each such path, if this path is:

    * A directory, this is the most recent time at which the recursive contents
      of this directory were created, modified, or deleted. Since this function
      operates recursively, this considers this directory itself and all
      transitive subdirectories and files of this directory.
    * A file, this is the most recent time at which the contents of this file
      were created or modified.
    * A symbolic link, this is the most recent time at which this symbolic link
      was created. Hence, this function does *not* follow symbolic links.

    Parameters
    -----------
    pathnames : tuple[str]
        Tuple of all relative and absolute paths to inspect.

    Returns
    -----------
    NumericTypes
        Mtime in seconds of the most recent path as either an integer or float,
        depending on the boolean returned by the platform-specific
        :func:`os.stat_float_times` function.
    '''

    # Avoid circular import dependencies.
    from betse.util.path import dirs

    # Return the maximum of all mtimes in the...
    return max(
        # Generator expression yielding the...
        (
            # If this path is a:
            # * Non-directory file, the mtime of this file.
            # * Directory, the mtime of the most recent path in this directory.
            dirs.get_mtime_newest(pathname) if dirs.is_dir(pathname) else
            get_mtime(pathname)
            # For each passed pathname.
            for pathname in pathnames
        )
    )

# ....................{ MOVERS                             }....................
@type_check
def move(pathname_source: str, pathname_target: str) -> None:
    '''
    Move the passed source to target path.

    Such path will be moved in a manner maximally preserving metadata (e.g.,
    owner, group, permissions, times, extended file system attributes).
    Likewise, if such source path is a symbolic link, such link (rather than its
    transitive target) will be moved and hence preserved.

    If either the source path does not exist *or* the target path already
    exists, an exception will be raised.
    '''

    # Log such move in a contextual manner.
    logs.log_debug(
        'Moving %s "%s" to "%s".',
        get_type_label(pathname_source), pathname_source, pathname_target)

    # Raise an exception unless the source path exists.
    die_unless_path(pathname_source)

    # Raise an exception if the target path already exists. This is essential to
    # sane cross-platform semantics. shutil.move() is implemented in terms of
    # os.rename(), which overwrites such path if such path is a non-directory
    # file depending on platform. In most cases, that's bad.
    die_if_path(pathname_target)

    # Perform such move.
    shutil.move(pathname_source, pathname_target)
