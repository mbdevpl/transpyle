"""Tests of C++ language support."""

import datetime
import logging
import pathlib
import unittest

# import typed_astunparse

# from transpyle.general.code_reader import CodeReader
from transpyle.cpp.compiler import CppSwigCompiler
from .examples import EXAMPLES_RESULTS_ROOT, EXAMPLES_CPP14_FILES

_LOG = logging.getLogger(__name__)


class Tests(unittest.TestCase):

    @unittest.skip('not ready yet')
    def test_compile_examples(self):
        # code_reader = CodeReader()
        compiler = CppSwigCompiler()
        for input_path in EXAMPLES_CPP14_FILES:
            output_dir = pathlib.Path(
                EXAMPLES_RESULTS_ROOT, input_path.parent.name,
                'f2py_tmp_{}'.format(datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')))
            if not output_dir.is_dir():
                output_dir.mkdir()
            with open(str(input_path)) as input_file:
                code = input_file.read()
            with self.subTest(input_path=input_path):
                output_path = compiler.compile(code, input_path, output_dir)
                self.assertIsInstance(output_path, pathlib.Path)
                output_path.unlink()
            try:
                output_dir.rmdir()
            except OSError:
                pass
