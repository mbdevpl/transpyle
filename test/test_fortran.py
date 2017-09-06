"""Tests for Fortran language support."""

import logging
import pathlib
import unittest

import typed_ast.ast3
import typed_astunparse

from transpyle.fortran.parser import FortranParser
from transpyle.fortran.ast_generalizer import FortranAstGeneralizer
from transpyle.fortran.unparser import FortranUnparser

_LOG = logging.getLogger(__name__)

_HERE = pathlib.Path(__file__).resolve().parent

EXAMPLES_F77 = list(_HERE.joinpath('examples', 'f77').glob('**/*.*'))
EXAMPLES_F95 = list(_HERE.joinpath('examples', 'f95').glob('**/*.*'))


class Tests(unittest.TestCase):

    def test_new_cases(self):
        """Optional tests for exeprimental or local files."""
        paths = [
            '~/Projects/fortran/flash-subset/FLASH4.4/source/physics/Hydro/HydroMain/simpleUnsplit/HLL/hy_hllUnsplit.F90'
            '']
        for path in paths:
            path = pathlib.Path(path)
            if not path.is_file():
                continue

    def test_parse(self):
        for input_path in EXAMPLES_F77 + EXAMPLES_F95:
            with self.subTest(input_path=input_path):
                parser = FortranParser()
                root_node = parser.parse(input_path, verbosity=100)
                self.assertIsNotNone(root_node)

    def test_generalize(self):
        #transformations_path = _HERE.joinpath('transformations')
        #transformations_path.mkdir(exist_ok=True)
        for input_path in EXAMPLES_F77:
            with self.subTest(input_path=input_path):
                parser = FortranParser()
                root_node = parser.parse(input_path, verbosity=100)
                self.assertIsNotNone(root_node)
                generalizer = FortranAstGeneralizer()
                tree = generalizer.generalize(root_node)
                self.assertIsInstance(tree, typed_ast.ast3.AST)
                typed_astunparse.dump(tree)
                #code = typed_astunparse.unparse(typed_tree)
                #self.assertGreater(len(code), 0)
                #result_path = transformations_path.joinpath(input_path.stem + '.py')
                #with open(result_path, 'w') as result_file:
                #    result_file.write(code)
                #_LOG.debug('```%s```', code)

    def test_unparse(self):
        for input_path in EXAMPLES_F77:
            with self.subTest(input_path=input_path):
                parser = FortranParser()
                root_node = parser.parse(input_path, verbosity=100)
                self.assertIsNotNone(root_node)
                generalizer = FortranAstGeneralizer()
                tree = generalizer.generalize(root_node)
                self.assertIsInstance(tree, typed_ast.ast3.AST)
                unparser = FortranUnparser()
                code = unparser.unparse(tree)
                self.assertIsInstance(code, str)
