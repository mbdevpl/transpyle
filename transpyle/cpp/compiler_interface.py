"""Interfaces to existing C++ compilers."""

from distutils.sysconfig import get_python_inc, get_config_vars
import pathlib
import typing as t

import numpy as np

from ..general import CompilerInterface
from ..general.tools import run_tool

PYTHON_LIB_PATH = pathlib.Path(get_python_inc(plat_specific=1))

PYTHON_CONFIG = get_config_vars()


def split_and_strip(text: str) -> t.List[str]:
    return tuple([_.strip() for _ in text.split() if _.strip()])


class GppInterface(CompilerInterface):

    """GNU C++ compiler interface."""

    _features = {'MPI', 'OpenMP'}

    _executables = {
        '': pathlib.Path('g++'),
        'MPI': pathlib.Path('mpic++')
    }

    _flags = {
        '': ('-O3', '-fPIC', '-Wall', '-Wextra', '-Wpedantic', '-fdiagnostics-color=always'),
        'compile': tuple(split_and_strip('{} {}'.format(
            PYTHON_CONFIG['BASECFLAGS'], PYTHON_CONFIG['BASECPPFLAGS']))),
        'link': (),
        'OpenMP': ('-fopenmp',)
    }
    # -Ofast

    include_paths = [
        pathlib.Path(PYTHON_CONFIG['INCLUDEPY']),
        *[pathlib.Path(_, 'core', 'include') for _ in np.__path__]]

    library_paths = [
        pathlib.Path(PYTHON_CONFIG['LIBDIR'])]

    ldlibrary = pathlib.Path(PYTHON_CONFIG['LDLIBRARY'].lstrip('lib')).with_suffix('')

    libraries = split_and_strip('-l{} {} {} {}'.format(
        ldlibrary, PYTHON_CONFIG['LIBS'], PYTHON_CONFIG['SYSLIBS'], PYTHON_CONFIG['LINKFORSHARED']))

    _options = {
        'compile': ['-I{}'.format(_) for _ in include_paths],
        'link': [*['-L{}'.format(_) for _ in library_paths], *libraries]
    }

    def _compile(self, code, path, output_folder, input_paths: t.Sequence[pathlib.Path], **kwargs):
        result = run_tool(self.executable('compile'), [
            *self.flags('compile'), *self.options('compile'),
            '-c', *[str(path) for path in input_paths]])
        return {'results': {'compile': result}}

    def _link(self, code, path, output_folder, input_paths: t.Sequence[pathlib.Path],
              output_path: pathlib.Path, **kwargs):
        input_paths = [path.with_suffix('.o') for path in input_paths]
        result = run_tool(self.executable('link'), [
            *self.flags('link'), *self.options('link'),
            '-shared', *[str(path) for path in input_paths], '-o', str(output_path)])
        return {'results': {'link': result, **kwargs['results']}}


class ClangppInterface(CompilerInterface):

    """LLVM C++ compiler (Clang++) interface."""

    _features = {'OpenMP'}

    _executables = {'': pathlib.Path('clang++')}

    _flags = {
        '': ('-O3', '-fPIC', '-Wall', '-Wextra', '-Wpedantic', '-fcolor-diagnostics'),
        'OpenMP': ('-fopenmp',)
    }
    # -Ofast
