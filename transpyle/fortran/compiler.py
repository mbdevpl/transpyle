"""Compiling Fortran code."""

import contextlib
import datetime
import io
import logging
import os
import pathlib
import subprocess
import tempfile
import typing as t

import argunparse
import numpy.f2py

from ..general import Compiler


_LOG = logging.getLogger(__name__)


def create_f2py_module_name(path: pathlib.Path) -> str:
    return '{}_transpyle_{}'.format(path.stem, datetime.datetime.now().strftime('%Y%m%d%H%M%S'))


class F2PyCompiler(Compiler):

    """Compile Fortran code into Python extension modules using f2py."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.argunparser = argunparse.ArgumentUnparser()

    def run_f2py(
            self, code: str, path: pathlib.Path, module_name: str,
            *args, **kwargs) -> subprocess.CompletedProcess:
        """Run f2py with given arguments."""
        assert isinstance(code, str), type(code)
        assert isinstance(path, pathlib.Path), type(path)
        assert isinstance(module_name, str), type(module_name)
        extra_args = self.argunparser.unparse(*args, **kwargs)
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            with contextlib.redirect_stderr(stderr):
                returncode = numpy.f2py.compile(
                    source=code, modulename=module_name, extra_args=extra_args,
                    verbose=False, source_fn=str(path), extension=path.suffix)
        result = subprocess.CompletedProcess(
            args='f2py -c -m {} {} {}'.format(module_name, extra_args, str(path)),
            returncode=returncode, stdout=stdout.getvalue(), stderr=stderr.getvalue())
        return result

    def compile(self, code: str, path: t.Optional[pathlib.Path] = None,
                output_folder: t.Optional[pathlib.Path] = None, **kwargs) -> pathlib.Path:
        """Compile Fortran code using f2py.

        Recognized kwargs:
        mpi=True -- enable MPI support,
        openmp=True -- enable OpenMP support.
        """
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
        # if __debug__:
        _LOG.warning('f2py compiling file: "%s", (%i characters)', path, len(code))
        # _LOG.debug('compiled file\'s contents: %s', code)

        # module_name = cls.create_module_name(code, file_name)
        # if __debug__:
        _LOG.debug('f2py desired module name: %s', module_name)

        # if 'debug' in extra_args or 'debug-capi' in extra_args:
        #    _LOG.warning('building f2py module in debug mode')

        if kwargs.get('mpi', False):
            # kwargs['f77exec'] = 'mpif90'
            kwargs['f90exec'] = 'mpif90'
            # kwargs['f77flags'] = '-g0'
            # kwargs['f90flags'] = '-g0'
        kwargs['opt'] = '-O3 -funroll-loops'
        if kwargs.get('openmp', False):
            kwargs['opt'] += ' -fopenmp'
        args = ()
        # args = (*args, '-v')
        # kwargs['noopt'] = True
        _working_dir = pathlib.Path.cwd()
        os.chdir(str(output_folder))
        result = self.run_f2py(code, path, module_name, *args, **kwargs)
        os.chdir(str(_working_dir))

        # if __debug__:
        # if result.returncode == 0:
        _LOG.debug('f2py result: %s', result)
        # else:
        #    _LOG.error(F2PY_ERROR_REPORT_FMT, result.returncode, result.stdout, result.stderr)

        if result.returncode != 0:
            raise RuntimeError(
                '{} returned a non-zero status: {}\nstdout="""{}"""\nstderr={}'
                .format(result.args, result.returncode, result.stdout, result.stderr))
        # print(result.args)
        # print(result.returncode)
        # print(result.stdout)
        # print(result.stderr)

        results = [result for result in output_folder.glob('{}*'.format(module_name))
                   if result.is_file()]
        if len(results) != 1:
            _LOG.warning('%s', result.args)
            _LOG.warning('%s', result.stdout)
            _LOG.error('%s', result.stderr)
        assert len(results) == 1, results
        return results[0]
