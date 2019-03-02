"""Tests for Fortran language support."""

import datetime
import logging
import pathlib
import types
import unittest

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
