
import logging
import os
# import pathlib
import platform
import unittest

# from encrypted_config.path_tools import normalize_path
from encrypted_config.json_io import json_to_file
import numba
import numpy as np
import timing

from transpyle.general import Language, AutoTranspiler
from transpyle.general import Binder
from transpyle.cpp import CppSwigCompiler
from transpyle.fortran import F2PyCompiler

from .common import EXAMPLES_ROOTS, RESULTS_ROOT

_LOG = logging.getLogger(__name__)
_TIME = timing.get_timing_group(__name__)

PERFORMANCE_RESULTS_ROOT = RESULTS_ROOT.joinpath('performance')

if not PERFORMANCE_RESULTS_ROOT.is_dir():
    PERFORMANCE_RESULTS_ROOT.mkdir()


class Tests(unittest.TestCase):

    def test_do_nothing(self):
        # reader = CodeReader()
        compiler_f95 = F2PyCompiler()
        binder = Binder()

        name = 'do_nothing'
        variants = {}
        variants['py'] = (EXAMPLES_ROOTS['python3'].joinpath(name + '.py'), None)
        path_f95 = EXAMPLES_ROOTS['f95'].joinpath(name + '.f90')
        variants['f95'] = (compiler_f95.compile_file(path_f95), None)
        if platform.system() == 'Linux':
            compiler_cpp = CppSwigCompiler()
            path_cpp = EXAMPLES_ROOTS['cpp14'].joinpath(name + '.cpp')
            variants['cpp'] = (compiler_cpp.compile_file(path_cpp), None)
        variants['py_numba'] = (variants['py'][0], numba.jit)

        for variant, (path, transform) in variants.items():
            with binder.temporarily_bind(path) as binding:
                tested_function = getattr(binding, name)
                if transform:
                    tested_function = transform(tested_function)
                with self.subTest(variant=variant, path=path):
                    # with _TIME.measure('{}.{}'.format(name, variant)) as timer:
                    for _ in _TIME.measure_many('{}.{}'.format(name, variant), 1000):
                        tested_function()
                    # _LOG.warning('timing: %s', timer)

        timings_name = '.'.join([__name__, name])
        summary = timing.query_cache(timings_name).summary
        _LOG.info('%s', summary)
        json_to_file(summary, PERFORMANCE_RESULTS_ROOT.joinpath(timings_name + '.json'))

        self.assertAlmostEqual(summary['py']['median'], summary['f95']['median'],
                               places=5 if os.environ.get('CI') else 6)
        if platform.system() == 'Linux':
            self.assertAlmostEqual(summary['py']['median'], summary['cpp']['median'],
                                   places=5 if os.environ.get('CI') else 6)

    # @unittest.skipUnless(platform.system() == 'Linux', 'tested only on Linux')
    def test_compute_pi(self):
        # reader = CodeReader()
        compiler_cpp = CppSwigCompiler()
        transpiler_py_to_f95 = AutoTranspiler(Language.find('Python 3'), Language.find('Fortran 95'))
        # transpiler_py_to_cpp = AutoTranspiler(Language.find('Python 3'), Language.find('C++14'))
        binder = Binder()

        name = 'compute_pi'
        variants = {}
        variants['py'] = (EXAMPLES_ROOTS['python3'].joinpath(name + '.py'), None)
        if platform.system() == 'Linux':
            path_cpp = EXAMPLES_ROOTS['cpp14'].joinpath(name + '.cpp')
            variants['cpp'] = (compiler_cpp.compile_file(path_cpp), None)
        # variants['py_to_cpp'] = transpiler_py_to_cpp.transpile_file(variants['py'])
        # variants['f95'] = EXAMPLES_ROOTS['f95']
        variants['py_to_f95'] = (transpiler_py_to_f95.transpile_file(variants['py'][0]), None)
        variants['py_numba'] = (variants['py'][0], lambda f: numba.jit(f))

        segments_list = [_ for _ in range(0, 20)]

        values = {}
        for segments in segments_list:
            values[segments] = {}

        for variant, (path, transform) in variants.items():
            with binder.temporarily_bind(path) as binding:
                tested_function = getattr(binding, name)
                if transform:
                    tested_function = transform(tested_function)
                for segments in segments_list:
                    with self.subTest(variant=variant, path=path, segments=segments):
                        for _ in _TIME.measure_many('{}.{}.{}'.format(name, segments, variant), 1000):
                            value = tested_function(segments)
                        if segments >= 17:
                            self.assertAlmostEqual(value, np.pi, places=5)
                        elif segments > 10:
                            self.assertAlmostEqual(value, np.pi, places=6)
                        elif segments > 4:
                            self.assertAlmostEqual(value, np.pi, places=3)
                        else:
                            self.assertAlmostEqual(value, np.pi, places=0)
                        values[segments][variant] = value
                        # _LOG.warning('timing: %s, value=%f', timer, value)

        for segments in segments_list:
            timings_name = '.'.join([__name__, name, str(segments)])
            summary = timing.query_cache(timings_name).summary
            _LOG.info('%s', summary)
            json_to_file(summary, PERFORMANCE_RESULTS_ROOT.joinpath(timings_name + '.json'))

        # for segments in segments_list:
        #    vals = list(values[segments].values())
        #    for val in vals:
        #        self.assertEqual(vals[0], val)

    def test_matmul(self):
        pass
