
import logging
# import pathlib
import platform
import unittest

# from encrypted_config.path_tools import normalize_path
from encrypted_config.json_io import json_to_file
import numpy as np
import timing

# from transpyle.general import CodeReader, Language, AutoTranspiler
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

    def test_empty_funciton(self):
        # reader = CodeReader()
        compiler_f = F2PyCompiler()
        compiler_cpp = CppSwigCompiler()
        binder = Binder()

        name = 'do_nothing'
        variants = {}
        variants['py'] = EXAMPLES_ROOTS['python3'].joinpath(name + '.py')
        path_f = EXAMPLES_ROOTS['f95'].joinpath(name + '.f90')
        variants['f'] = compiler_f.compile_file(path_f)
        if platform.system() == 'Linux':
            path_cpp = EXAMPLES_ROOTS['cpp14'].joinpath(name + '.cpp')
            variants['cpp'] = compiler_cpp.compile_file(path_cpp)

        for variant, path in variants.items():
            with binder.tempoararily_bind(path) as binding:
                with self.subTest(variant=variant, path=path):
                    for _ in _TIME.measure_many('{}.{}'.format(name, variant), 50):
                        binding.do_nothing()
                    # with _TIME.measure('{}.{}'.format(name, variant)) as timer:
                    #    # timer = _TIME.start('{}.{}'.format(name, variant))
                    #    binding.do_nothing()
                    #    # timer.stop()
                    # _LOG.warning('timing: %s', timer)

        timings_name = '.'.join([__name__, name])
        summary = timing.query_cache(timings_name).summary
        _LOG.info('%s', summary)
        json_to_file(summary, PERFORMANCE_RESULTS_ROOT.joinpath(timings_name + '.json'))

        self.assertAlmostEqual(summary['py']['median'], summary['f']['median'], places=6)
        if platform.system() == 'Linux':
            self.assertAlmostEqual(summary['py']['median'], summary['cpp']['median'], places=6)

    # @unittest.skipUnless(platform.system() == 'Linux', 'tested only on Linux')
    def test_compute_pi(self):
        # reader = CodeReader()
        compiler_cpp = CppSwigCompiler()
        # transpiler_py_to_cpp = AutoTranspiler(Language.find('Python 3'), Language.find('C++14'))
        binder = Binder()

        name = 'compute_pi'
        variants = {}
        variants['py'] = EXAMPLES_ROOTS['python3'].joinpath(name + '.py')
        if platform.system() == 'Linux':
            path_cpp = EXAMPLES_ROOTS['cpp14'].joinpath(name + '.cpp')
            variants['cpp'] = compiler_cpp.compile_file(path_cpp)
        # variants['py_to_cpp'] = transpiler_py_to_cpp.transpile_file(variants['py'])

        segments_list = [_ for _ in range(0, 20)]

        values = {}
        for segments in segments_list:
            values[segments] = {}

        for variant, path in variants.items():
            with binder.tempoararily_bind(path) as binding:
                for segments in segments_list:
                    with self.subTest(variant=variant, path=path, segments=segments):
                        with _TIME.measure('{}.{}.{}'.format(name, segments, variant)):
                            # timer = _TIME.start('{}.{}.{}'.format(name, segments, variant))
                            value = binding.compute_pi(segments)
                            # timer.stop()
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
