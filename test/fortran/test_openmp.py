"""Tests for OpenMP support in transpyle."""

import pathlib
import sys
import tempfile
import unittest

from transpyle.general.code_reader import CodeReader
from transpyle import Language
from transpyle import AutoTranspiler

from test.common import EXAMPLES_PY3_FILES, make_f2py_tmp_folder


class Tests(unittest.TestCase):

    @unittest.skipIf(sys.version_info[:2] < (3, 6), 'unsupported in Python < 3.6')
    def test_fortran(self):
        for path in EXAMPLES_PY3_FILES:
            if path.name == 'gemm_openmp.py':
                input_path = path
                break

        output_dir = make_f2py_tmp_folder(input_path)


        transpiler = AutoTranspiler(Language.find('Python'), Language.find('Fortran'))
        self.assertIsNotNone(transpiler)
        reader = CodeReader()

        with tempfile.NamedTemporaryFile(suffix='.f90', delete=False) as output_file:
            # TODO: this leaves garbage behind in /tmp/ but is neeeded by subsequent transpiler passes
            # code_writer = CodeWriter('.py')
            # target_inlined_path = pathlib.Path(output_file.name)
            # code_writer.write_file(target_inlined_code, target_inlined_path)
            output_path = pathlib.Path(output_file.name)

        compiled_path = transpiler.transpile(reader.read_file(input_path), input_path, output_path, output_dir)
        # TODO: run it
