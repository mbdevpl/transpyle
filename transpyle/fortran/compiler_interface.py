"""Interfaces to existing Fortran compilers."""

import logging
import pathlib

import argunparse
import numpy.f2py

from ..general import call_tool, CompilerInterface
from ..general.tools import temporarily_set_envvars

_LOG = logging.getLogger(__name__)


class GfortranInterface(CompilerInterface):

    """GNU Fortran compiler interface."""

    _features = {'MPI', 'OpenMP', 'OpenACC'}

    _executables = {
        '': pathlib.Path('gfortran'),
        'MPI': pathlib.Path('mpifort')}

    _flags = {
        '': (
            '-O3', '-fPIC', '-funroll-loops', '-Wall', '-Wextra', '-Wpedantic',
            '-fdiagnostics-color=always'),
        # '-ffree-form',
        'OpenMP': ('-fopenmp',),
        'OpenACC': ('-fopenacc',)
        # '-foffload-force'
    }

    _options = {
        'OpenMP': ('-lgomp',),
        'OpenACC': ('-lgomp',)
    }


class PgifortranInterface(CompilerInterface):

    """PGI Fortran compiler interface."""

    _features = {'MPI', 'OpenMP', 'OpenACC'}

    _executables = {
        '': pathlib.Path('pgfortran'),
        'MPI': pathlib.Path('pgmpifortran')}

    _flags = {
        '': ('-O', '4', '-fPIC', '-fast',
             '-Minfo=all'),
        'OpenMP': ('-mp',),
        'OpenACC': ('-acc', '-Mvect=simd', '-Mcache_align', '-Mflushz', '-Mpre', '-ta=tesla', '-ta=tesla:nordc')
    }

    libraries = {
        'OpenMP': ('gomp',),
        'OpenACC': ('accapi', 'accg', 'accn', 'accg2', 'cudadevice',)
    }

    _options = {
        'OpenMP': ['-l{}'.format(_) for _ in libraries['OpenMP']],
        'OpenACC': ['-l{}'.format(_) for _ in libraries['OpenACC']],
    }


class F2pyInterface(CompilerInterface):

    """f2py compiler wrapper interface."""

    step_names = ['compile']

    _executables = {'': pathlib.Path('f2py')}

    _flags = {
        # 'compile': ('-fPIC',)
        # 'debug': ('debug', 'debug-capi')
    }

    _options = {
        '': ('-DNPY_NO_DEPRECATED_API=NPY_1_7_API_VERSION', '-DNPY_DISTUTILS_APPEND_FLAGS=1')}

    def __init__(self, f_compiler: CompilerInterface = None, *args, **kwargs):
        self.argunparser = argunparse.ArgumentUnparser()
        if f_compiler is None:
            f_compiler = GfortranInterface()
        self.f_compiler = f_compiler
        super().__init__(*args, **kwargs)

    def _compile(self, code: str, path: pathlib.Path, output_folder: pathlib.Path,
                 module_name: str, **kwargs):
        assert isinstance(code, str), type(code)
        assert isinstance(path, pathlib.Path), type(path)
        assert isinstance(module_name, str), type(module_name)

        f2py_args = self.flags('compile') + self.options('compile') \
            + self.f_compiler.options('compile')
        f2py_kwargs = {
            'f90exec': self.f_compiler.executable('compile'),
            'opt': ' '.join(self.f_compiler.flags('compile'))
        }
        # f2py_kwargs['noopt'] = True
        if isinstance(self.f_compiler, PgifortranInterface):
            f2py_kwargs['compiler'] = 'unix'
            f2py_kwargs['fcompiler'] = 'pg'
        extra_args = self.argunparser.unparse(*f2py_args, **f2py_kwargs)

        _LOG.info('f2py compiling file: "%s", (%i characters)', path, len(code))
        _LOG.debug('f2py extra args: %s', extra_args)
        # _LOG.debug('compiled file\'s contents: %s', code)
        # flgs = self.f_compiler.options('compile') + self.f_compiler.flags('compile')
        f2py_envvars = {
            # 'FFLAGS': self.argunparser.unparse(*flgs),
            # 'LDFLAGS': self.argunparser.unparse(*flgs),
            'NPY_DISTUTILS_APPEND_FLAGS': '1'}
        f2py_compile_kwargs = {
            'source': code, 'modulename': module_name, 'extra_args': extra_args, 'verbose': False,
            'source_fn': '{}'.format(path).replace(' ', '\\ '), 'extension': path.suffix}
        f2py_cmd_equivalent = 'f2py -c -m {} {} "{}"'.format(module_name, extra_args, path)
        with temporarily_set_envvars(**f2py_envvars):
            result = call_tool(numpy.f2py.compile, kwargs=f2py_compile_kwargs, cwd=output_folder,
                               commandline_equivalent=f2py_cmd_equivalent, capture_output=True)
        return {'result': result}
