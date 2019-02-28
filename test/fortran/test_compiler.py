"""Tests for Fortran language support."""

import datetime
import logging
import pathlib
import shutil
import types
import unittest

from encrypted_config.json_io import json_to_file
import numpy as np
import timing

from transpyle.general.binder import Binder
from transpyle.fortran.compiler import F2PyCompiler

from test.common import \
    EXAMPLES_RESULTS_ROOT, EXAMPLES_F77_FILES, EXAMPLES_F95_FILES

_LOG = logging.getLogger(__name__)
_TIME = timing.get_timing_group(__name__)


class Tests(unittest.TestCase):

    def test_compile(self):
        compiler = F2PyCompiler()
        binder = Binder()
        for input_path in [_ for _ in EXAMPLES_F77_FILES + EXAMPLES_F95_FILES
                           if _.name in ('addition.f90', 'do_nothing.f90')]:
            output_dir = pathlib.Path(
                EXAMPLES_RESULTS_ROOT, input_path.parent.name,
                'f2py_tmp_{}'.format(datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')))
            if not output_dir.is_dir():
                output_dir.mkdir()
            with open(str(input_path)) as input_file:
                code = input_file.read()
            with self.subTest(input_path=input_path):
                output_path = compiler.compile(code, input_path, output_dir)
                with binder.temporarily_bind(output_path) as binding:
                    self.assertIsInstance(binding, types.ModuleType)
                output_path.unlink()
            try:
                output_dir.rmdir()
            except OSError:
                pass

    def test_directives(self):
        # from transpyle.general.language import Language
        # from transpyle.general.transpiler import AutoTranspiler
        from test.common import EXAMPLES_ROOTS, RESULTS_ROOT

        PERFORMANCE_RESULTS_ROOT = RESULTS_ROOT.joinpath('performance')

        binder = Binder()
        compiler_f95 = F2PyCompiler()
        compiler_f95_omp = F2PyCompiler()
        compiler_f95_acc = F2PyCompiler()
        compiler_f95_acc.f2py.fortran_compiler_executable = 'pgfortran'
        # transpiler_py_to_f95 = AutoTranspiler(
        #    Language.find('Python 3'), Language.find('Fortran 95'))

        name = 'itemwise_calc'
        variants = {}
        # variants['py'] = (EXAMPLES_ROOTS['python3'].joinpath(name + '.py'), None)
        variants['f95'] = (
            compiler_f95.compile_file(EXAMPLES_ROOTS['f95'].joinpath(name + '.f90')), None)
        variants['f95_openmp'] = (
            compiler_f95_omp.compile_file(
                EXAMPLES_ROOTS['f95'].joinpath(name + '_openmp.f90')), None)
        if shutil.which(compiler_f95_acc.f2py.fortran_compiler_executable) is not None:
            variants['f95_openacc'] = (
                compiler_f95_acc.compile_file(
                    EXAMPLES_ROOTS['f95'].joinpath(name + '_openacc.f90')), None)
        # variants['py_to_f95'] = (transpiler_py_to_f95.transpile_file(variants['py'][0]), None)
        # variants['py_numba'] = (variants['py'][0], lambda f: numba.jit(f))
        # variants['numpy'] = (variants['py'][0], lambda f: np.copy)

        arrays = [np.array(np.random.random_sample((array_size,)), dtype=np.double)
                  for array_size in range(1024, 1024 * 64 + 1, 1024 * 4)]

        for variant, (path, transform) in variants.items():
            with binder.temporarily_bind(path) as binding:
                tested_function = getattr(binding, name)
                if transform:
                    tested_function = transform(tested_function)
                # import ipdb; ipdb.set_trace()
                for array in arrays:
                    with self.subTest(variant=variant, path=path, array_size=array.size):
                        # with _TIME.measure('{}.{}.{}'.format(name, segments, variant)):
                        for _ in _TIME.measure_many('{}.{}.{}'.format(name, array.size, variant), 50):
                            results = tested_function(array)
                        # self.assertListEqual(array.tolist(), array_copy.tolist())
                        self.assertTrue(results.shape, array.shape)

        for array in arrays:
            timings_name = '.'.join([__name__, name, str(array.size)])
            summary = timing.query_cache(timings_name).summary
            _LOG.info('%s', summary)
            json_to_file(summary, PERFORMANCE_RESULTS_ROOT.joinpath(timings_name + '.json'))

    def test_openmp(self):
        compiler = F2PyCompiler()
        binder = Binder()
        for input_path in [_ for _ in EXAMPLES_F77_FILES + EXAMPLES_F95_FILES]:
            if input_path.name == 'matmul_openmp.f':
                break
        output_dir = pathlib.Path(
            EXAMPLES_RESULTS_ROOT, input_path.parent.name,
            'f2py_tmp_{}'.format(datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')))
        if not output_dir.is_dir():
            output_dir.mkdir()
        with open(str(input_path)) as input_file:
            code = input_file.read()
        # with self.subTest(input_path=input_path):

        output_path = compiler.compile(code, input_path, output_dir, openmp=False)
        with binder.temporarily_bind(output_path) as binding:
            self.assertIsInstance(binding, types.ModuleType)
            with _TIME.measure('matmul-simple'):
                ret_val = binding.intmatmul(20, 1024, 1024)
        self.assertEqual(ret_val, 0)
        output_path.unlink()

        output_path = compiler.compile(code, input_path, output_dir, openmp=True)
        with binder.temporarily_bind(output_path) as binding:
            self.assertIsInstance(binding, types.ModuleType)
            with _TIME.measure('matmul-openmp'):
                ret_val = binding.intmatmul(20, 1024, 1024)
        self.assertEqual(ret_val, 0)
        _LOG.warning('%s', _TIME.summary)
        output_path.unlink()

        try:
            output_dir.rmdir()
        except OSError:
            pass
