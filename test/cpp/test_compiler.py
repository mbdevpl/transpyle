"""Tests of C++ compilation."""

import datetime
import logging
import pathlib
import platform
import unittest

import timing

from transpyle.general.binder import Binder
from transpyle.cpp.compiler import CppSwigCompiler

from test.common import EXAMPLES_RESULTS_ROOT, EXAMPLES_CPP14_FILES

_LOG = logging.getLogger(__name__)
_TIME = timing.get_timing_group(__name__)


class Tests(unittest.TestCase):

    @unittest.skipUnless(platform.system() == 'Linux', 'tested only on Linux')
    def test_compile_examples(self):
        compiler = CppSwigCompiler()
        for input_path in EXAMPLES_CPP14_FILES:
            output_dir = pathlib.Path(
                EXAMPLES_RESULTS_ROOT, input_path.parent.name,
                'swig_tmp_{}'.format(datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')))
            if not output_dir.is_dir():
                output_dir.mkdir()
            with input_path.open() as input_file:
                code = input_file.read()
            with self.subTest(input_path=input_path):
                output_path = compiler.compile(code, input_path, output_dir)
                self.assertIsInstance(output_path, pathlib.Path)
                binder = Binder()
                with binder.temporarily_bind(output_path) as binding:
                    self.assertIsNotNone(binding)
                output_path.unlink()
            try:
                output_dir.rmdir()
            except OSError:
                pass

    def test_openmp(self):
        compiler = CppSwigCompiler()
        for input_path in EXAMPLES_CPP14_FILES:
            if input_path.name == 'matmul_openmp.cpp':
                break
        output_dir = pathlib.Path(
            EXAMPLES_RESULTS_ROOT, input_path.parent.name,
            'swig_tmp_{}'.format(datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')))
        if not output_dir.is_dir():
            output_dir.mkdir()
        with input_path.open() as input_file:
            code = input_file.read()
        output_path = compiler.compile(code, input_path, output_dir)
        self.assertIsInstance(output_path, pathlib.Path)
        binder = Binder()
        with binder.temporarily_bind(output_path) as binding:
            print(type(binding.multiply_martices_example))
            # print(help(binding.main))
            with _TIME.measure('matmul') as timer:
                ret_val = binding.multiply_martices_example(1, 3000, 3000)
            self.assertEqual(ret_val, 0)
            _LOG.warning('%s', _TIME.summary)
            self.assertIsNotNone(binding)
        output_path.unlink()
        try:
            output_dir.rmdir()
        except OSError:
            pass
