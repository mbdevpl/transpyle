"""Integration tests for translating between Fortran and other languages."""

import pathlib
import sys
import unittest

from transpyle.general.code_reader import CodeReader
from transpyle.general.code_writer import CodeWriter

from transpyle.fortran.parser import FortranParser
from transpyle.fortran.ast_generalizer import FortranAstGeneralizer
from transpyle.fortran.unparser import Fortran77Unparser

from transpyle.python.parser import TypedPythonParserWithComments
from transpyle.python.unparser import TypedPythonUnparserWithComments

from test.common import EXAMPLES_F77_FILES, EXAMPLES_PY3_FILES


class Tests(unittest.TestCase):

    def test_fortran_to_python(self):
        for input_path in EXAMPLES_F77_FILES:
            reader = CodeReader()
            parser = FortranParser()
            generalizer = FortranAstGeneralizer()
            unparser = TypedPythonUnparserWithComments()
            writer = CodeWriter('.py')
            with self.subTest(input_path=input_path):
                code = reader.read_file(input_path)
                fortran_ast = parser.parse(code, input_path)
                tree = generalizer.generalize(fortran_ast)
                python_code = unparser.unparse(tree)
                writer.write_file(python_code, pathlib.Path('/tmp', input_path.name + '.py'))

    @unittest.skip('not ready yet')
    def test_python_to_fortran(self):
        for input_path in EXAMPLES_PY3_FILES:
            reader = CodeReader()
            parser = TypedPythonParserWithComments()
            unparser = Fortran77Unparser()
            writer = CodeWriter('.f')
            with self.subTest(input_path=input_path):
                python_code = reader.read_file(input_path)
                tree = parser.parse(python_code, input_path, mode='exec')
                fortran_code = unparser.unparse(tree)
                writer.write_file(fortran_code, pathlib.Path('/tmp', input_path.name + '.f'))

    @unittest.skipIf(sys.version_info[:2] < (3, 6), 'requires Python >= 3.6')
    def test_fortran_to_python_to_fortran(self):
        for input_path in EXAMPLES_F77_FILES:
            parser = FortranParser()
            generalizer = FortranAstGeneralizer()
            unparser = TypedPythonUnparserWithComments()
            python_parser = TypedPythonParserWithComments(default_mode='exec')
            writer = CodeWriter('.f')
            with self.subTest(input_path=input_path):
                fortran_ast = parser.parse('', input_path)
                tree = generalizer.generalize(fortran_ast)
                python_code = unparser.unparse(tree)
                tree = python_parser.parse(python_code)
                fortran_code = unparser.unparse(tree)
                writer.write_file(fortran_code, pathlib.Path('/tmp', input_path.name + '.py.f'))
