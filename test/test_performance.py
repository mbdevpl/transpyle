
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

from .common import EXAMPLES_ROOTS, PERFORMANCE_RESULTS_ROOT

_LOG = logging.getLogger(__name__)
_TIME = timing.get_timing_group(__name__)


class Tests(unittest.TestCase):

    def test_do_nothing(self):
        name = 'do_nothing'
        variants = {
            'py': EXAMPLES_ROOTS['python3'].joinpath(name + '.py'),
            'f95': F2PyCompiler().compile_file(EXAMPLES_ROOTS['f95'].joinpath(name + '.f90'))}
        variants['py_numba'] = variants['py']
        if platform.system() == 'Linux':
            variants['cpp'] = CppSwigCompiler().compile_file(
                EXAMPLES_ROOTS['cpp14'].joinpath(name + '.cpp'))

        transforms = {'py_numba': numba.jit}

        binder = Binder()
        for variant, path in variants.items():
            with binder.temporarily_bind(path) as binding:
                tested_function = getattr(binding, name)
                if variant in transforms:
                    tested_function = transforms[variant](tested_function)
                with self.subTest(variant=variant, path=path):
                    # with _TIME.measure('{}.{}'.format(name, variant)) as timer:
                    for _ in _TIME.measure_many('{}.{}'.format(name, variant), 1000):
                        tested_function()
                    # _LOG.warning('timing: %s', timer)

        timings_name = '.'.join([__name__, name])
        summary = timing.query_cache(timings_name).summary
        _LOG.info('%s', summary)
        json_to_file(summary, PERFORMANCE_RESULTS_ROOT.joinpath(timings_name + '.json'))

        if summary['py']['median'] < summary['f95']['median']:
            self.assertAlmostEqual(summary['py']['median'], summary['f95']['median'],
                                   places=5 if os.environ.get('CI') else 6)
        if platform.system() == 'Linux':
            if summary['py']['median'] < summary['cpp']['median']:
                self.assertAlmostEqual(summary['py']['median'], summary['cpp']['median'],
                                       places=5 if os.environ.get('CI') else 6)

    # @unittest.skipUnless(platform.system() == 'Linux', 'tested only on Linux')
    def test_compute_pi(self):
        name = 'compute_pi'

        # t.Dict[str, pathlib.Path]
        variants = {
            'py': EXAMPLES_ROOTS['python3'].joinpath(name + '.py'),
            'f95': F2PyCompiler().compile_file(EXAMPLES_ROOTS['f95'].joinpath(name + '.f90'))
        }
        variants['py_numba'] = variants['py']
        variants['py_to_f95'] = AutoTranspiler(
            Language.find('Python'), Language.find('Fortran 95')).transpile_file(variants['py'])
        if platform.system() == 'Linux':
            variants['cpp'] = CppSwigCompiler().compile_file(
                EXAMPLES_ROOTS['cpp14'].joinpath(name + '.cpp'))
            variants['py_to_cpp'] = AutoTranspiler(
                Language.find('Python'), Language.find('C++14')).transpile_file(variants['py'])

        # t.Dict[str, collections.abc.Callable]
        transforms = {'py_numba': numba.jit}

        segments_list = [_ for _ in range(0, 20)]

        # values = {}
        # for segments in segments_list:
        #     values[segments] = {}

        binder = Binder()
        for variant, path in variants.items():
            with binder.temporarily_bind(path) as binding:
                tested_function = getattr(binding, name)
                if variant in transforms:
                    tested_function = transforms[variant](tested_function)
                for segments in segments_list:
                    with self.subTest(variant=variant, path=path, segments=segments):
                        for _ in _TIME.measure_many(
                                '{}.{}.{}'.format(name, segments, variant), 1000):
                            value = tested_function(segments)
                        if segments >= 17:
                            self.assertAlmostEqual(value, np.pi, places=5)
                        elif segments > 10:
                            self.assertAlmostEqual(value, np.pi, places=6)
                        elif segments > 4:
                            self.assertAlmostEqual(value, np.pi, places=3)
                        else:
                            self.assertAlmostEqual(value, np.pi, places=0)
                        # values[segments][variant] = value
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

    def test_copy_array(self):
        name = 'copy_array'
        variants = {
            'py': EXAMPLES_ROOTS['python3'].joinpath(name + '.py'),
            'f95': F2PyCompiler().compile_file(EXAMPLES_ROOTS['f95'].joinpath(name + '.f90'))}
        variants['py_numba'] = variants['py']
        variants['numpy'] = variants['py']
        if platform.system() == 'Linux':
            # variants['cpp'] = CppSwigCompiler().compile_file(
            #     EXAMPLES_ROOTS['cpp14'].joinpath(name + '.cpp'))
            # variants['py_to_cpp'] = AutoTranspiler(
            #     Language.find('Python 3'), Language.find('C++14')).transpile_file(variants['py'])
            pass
        # variants['py_to_f95'] = AutoTranspiler(
        #     Language.find('Python'), Language.find('Fortran 95')).transpile_file(variants['py'])

        transforms = {'py_numba': numba.jit, 'numpy': lambda _: np.copy}

        arrays = [np.array(np.random.random_sample((array_size,)), dtype=np.double)
                  for array_size in range(1024, 1024 * 64 + 1, 1024 * 4)]

        binder = Binder()
        for variant, path in variants.items():
            with binder.temporarily_bind(path) as binding:
                tested_function = getattr(binding, name)
                if variant in transforms:
                    tested_function = transforms[variant](tested_function)
                for array in arrays:
                    with self.subTest(variant=variant, path=path, array_size=array.size):
                        # with _TIME.measure('{}.{}.{}'.format(name, segments, variant)):
                        for _ in _TIME.measure_many(
                                '{}.{}.{}'.format(name, array.size, variant), 50):
                            array_copy = tested_function(array)
                        self.assertListEqual(array.tolist(), array_copy.tolist())

        for array in arrays:
            timings_name = '.'.join([__name__, name, str(array.size)])
            summary = timing.query_cache(timings_name).summary
            _LOG.info('%s', summary)
            json_to_file(summary, PERFORMANCE_RESULTS_ROOT.joinpath(timings_name + '.json'))
