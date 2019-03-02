"""Compiling Fortran code."""

# import contextlib
import datetime
# import io
import logging
import pathlib
import subprocess
import tempfile
import typing as t

import argunparse
import numpy.f2py

from ..general import Compiler
from ..general.tools import temporarily_change_dir, call_tool


_LOG = logging.getLogger(__name__)


def create_f2py_module_name(path: pathlib.Path) -> str:
    return '{}_transpyle_{}'.format(path.stem, datetime.datetime.now().strftime('%Y%m%d%H%M%S'))


class F2pyInterface:

    fortran_compiler_executable = 'gfortran'
    gfortran_flags = ('-O3', '-funroll-loops', '-fopenmp', '-Wall', '-Wextra', '-Wpedantic')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.argunparser = argunparse.ArgumentUnparser()

    def compile(
            self, code: str, path: pathlib.Path, output_folder: pathlib.Path, module_name: str,
            *args, **kwargs) -> subprocess.CompletedProcess:
        """Run f2py with given arguments."""
        assert isinstance(code, str), type(code)
        assert isinstance(path, pathlib.Path), type(path)
        assert isinstance(module_name, str), type(module_name)

        # args = (*args, '-v')
        args = (*args, '-DNPY_NO_DEPRECATED_API=NPY_1_7_API_VERSION')
        args = (*args, '-lgomp')
        # kwargs['f90exec'] = # 'mpif90'
        if 'f90exec' not in kwargs and self.fortran_compiler_executable is not None:
            kwargs['f90exec'] = self.fortran_compiler_executable
        if 'opt' not in kwargs:
            kwargs['opt'] = ''
        else:
            kwargs['opt'] += ' '
        # kwargs['noopt'] = True
        kwargs['opt'] += ' '.join(self.gfortran_flags)
        extra_args = self.argunparser.unparse(*args, **kwargs)
        _LOG.warning('f2py compiling file: "%s", (%i characters)', path, len(code))
        # _LOG.debug('compiled file\'s contents: %s', code)

        return call_tool(
            numpy.f2py.compile, kwargs={
                'source': code, 'modulename': module_name, 'extra_args': extra_args,
                'verbose': False, 'source_fn': '{}'.format(path).replace(' ', '\\ '),
                'extension': path.suffix},
            cwd=output_folder,
            commandline_equivalent='f2py -c -m {} {} "{}"'.format(module_name, extra_args, path))


class F2PyCompiler(Compiler):

    """Compile Fortran code into Python extension modules using f2py."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.argunparser = argunparse.ArgumentUnparser()
        self.f2py = F2pyInterface()

    def compile(self, code: str, path: t.Optional[pathlib.Path] = None,
                output_folder: t.Optional[pathlib.Path] = None, **kwargs) -> pathlib.Path:
        """Compile Fortran code using f2py.

        Recognized kwargs:
        mpi=True -- enable MPI support,
        openmp=True -- enable OpenMP support.
        """
        # kwargs |= self.default_kwargs
        if output_folder is None:
            with tempfile.TemporaryDirectory() as tmpdir:
                output_folder = pathlib.Path(tmpdir)
            output_folder.mkdir()

        assert isinstance(code, str), type(code)
        assert isinstance(path, pathlib.Path), type(path)
        assert path.is_file(), path
        assert isinstance(output_folder, pathlib.Path), type(output_folder)
        assert output_folder.is_dir(), output_folder

        module_name = create_f2py_module_name(path)
        _LOG.debug('f2py desired module name: %s', module_name)

        # if 'debug' in extra_args or 'debug-capi' in extra_args:
        #    _LOG.warning('building f2py module in debug mode')

        if kwargs.get('mpi', False):
            # kwargs['f77exec'] = 'mpif90'
            kwargs['f90exec'] = 'mpif90'
            # kwargs['f77flags'] = '-g0'
            # kwargs['f90flags'] = '-g0'
            del kwargs['mpi']
        if 'openmp' in kwargs:
            if kwargs['openmp']:
                kwargs['opt'] = '-fopenmp'
            del kwargs['openmp']

        with temporarily_change_dir(output_folder):
            result = self.f2py.compile(code, path, output_folder, module_name, **kwargs)

        path_mask = '{}*'.format(module_name)
        output_paths = [output_path for output_path in output_folder.glob(path_mask)
                        if output_path.is_file()]
        if len(output_paths) != 1:
            raise ValueError(
                'expected 1 output path matching "{}" but {} found: {}\nf2py result: {}'
                .format(path_mask, len(output_paths), output_paths, result))
        return output_paths[0]
