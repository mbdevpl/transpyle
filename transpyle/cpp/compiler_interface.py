"""Interfaces to existing C++ compilers."""

import collections
from distutils.sysconfig import get_python_inc, get_config_vars
import pathlib
import platform
import typing as t

import numpy as np

from ..general import CompilerInterface

PYTHON_LIB_PATH = pathlib.Path(get_python_inc(plat_specific=1))

PYTHON_CONFIG = get_config_vars()

if platform.system() == 'Windows':
    PYTHON_CONFIG = collections.defaultdict(str, PYTHON_CONFIG.items())


def split_and_strip(text: str) -> t.List[str]:
    return tuple([_.strip() for _ in text.split() if _.strip()])


class GppInterface(CompilerInterface):

    """GNU C++ compiler interface."""

    _features = {'MPI', 'OpenMP'}

    _executables = {
        '': pathlib.Path('g++'),
        'MPI': pathlib.Path('mpic++')
    }

    compile_flags = tuple()

    # Config does not always contain these items (eg. on Windows)

    if 'BASECFLAGS' in PYTHON_CONFIG:
        compile_flags = tuple(split_and_strip('{} {}'.format(compile_flags,PYTHON_CONFIG['BASECFLAGS'])))

    if 'BASECPPFLAGS' in PYTHON_CONFIG:
        compile_flags = tuple(split_and_strip('{} {}'.format(compile_flags,PYTHON_CONFIG['BASECPPFLAGS'])))

    _flags = {
        '': ('-O3', '-fPIC', '-Wall', '-Wextra', '-Wpedantic', '-fdiagnostics-color=always'),
        'compile': compile_flags,
        'link': (),
        'OpenMP': ('-fopenmp',)
    }
    # -Ofast

    include_paths = [
        pathlib.Path(PYTHON_CONFIG['INCLUDEPY']),
        *[pathlib.Path(_, 'core', 'include') for _ in np.__path__]]

    library_paths = []
    if 'LIBDIR' in PYTHON_CONFIG:
        library_paths.append(pathlib.Path(PYTHON_CONFIG['LIBDIR']))

    if 'LDLIBRARY' in PYTHON_CONFIG:
        ldlibrary = pathlib.Path(PYTHON_CONFIG['LDLIBRARY'].lstrip('lib')).with_suffix('')
    else:
        ldlibrary = None

    if 'LIBS' in PYTHON_CONFIG and 'SYSLIBS' in PYTHON_CONFIG and 'LINKFORSHARED' in PYTHON_CONFIG:
        libraries = split_and_strip('-l{} {} {} {}'.format(
            ldlibrary, PYTHON_CONFIG['LIBS'], PYTHON_CONFIG['SYSLIBS'], PYTHON_CONFIG['LINKFORSHARED']))
    else:
        libraries = []

    _options = {
        'compile': ['-I{}'.format(_) for _ in include_paths],
        'link': [*['-L{}'.format(_) for _ in library_paths], *libraries]
    }


class ClangppInterface(CompilerInterface):

    """LLVM C++ compiler (Clang++) interface."""

    _features = {'OpenMP'}

    _executables = {'': pathlib.Path('clang++')}

    compile_flags = tuple()

    # Config does not always contain these items (eg. on Windows)

    if 'BASECFLAGS' in PYTHON_CONFIG:
        compile_flags = tuple(split_and_strip('{} {}'.format(compile_flags, PYTHON_CONFIG['BASECFLAGS'])))

    if 'BASECPPFLAGS' in PYTHON_CONFIG:
        compile_flags = tuple(split_and_strip('{} {}'.format(compile_flags, PYTHON_CONFIG['BASECPPFLAGS'])))

    _flags = {
        '': ('-O3', '-fPIC', '-Wall', '-Wextra', '-Wpedantic', '-fcolor-diagnostics'),
        'compile': compile_flags,
        'OpenMP': ('-fopenmp',)
    }
    # -Ofast

    include_paths = [
        pathlib.Path(PYTHON_CONFIG['INCLUDEPY']),
        *[pathlib.Path(_, 'core', 'include') for _ in np.__path__]]

    library_paths = []
    if 'LIBDIR' in PYTHON_CONFIG:
        library_paths.append(pathlib.Path(PYTHON_CONFIG['LIBDIR']))

    if 'LDLIBRARY' in PYTHON_CONFIG:
        ldlibrary = pathlib.Path(PYTHON_CONFIG['LDLIBRARY'].lstrip('lib')).with_suffix('')
    else:
        ldlibrary = None

    if 'LIBS' in PYTHON_CONFIG and 'SYSLIBS' in PYTHON_CONFIG and 'LINKFORSHARED' in PYTHON_CONFIG:
        libraries = split_and_strip('-l{} {} {} {}'.format(
            ldlibrary, PYTHON_CONFIG['LIBS'], PYTHON_CONFIG['SYSLIBS'], PYTHON_CONFIG['LINKFORSHARED']))
    else:
        libraries = []

    _options = {
        'compile': ['-I{}'.format(_) for _ in include_paths],
        'link': [*['-L{}'.format(_) for _ in library_paths], *libraries]
    }
