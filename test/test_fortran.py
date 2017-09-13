"""Tests for Fortran language support."""

import logging
import pathlib
import unittest

import typed_ast.ast3
import typed_astunparse

from transpyle.fortran.parser import FortranParser
from transpyle.fortran.ast_generalizer import FortranAstGeneralizer
from transpyle.fortran.unparser import Fortran77Unparser
from .examples import EXAMPLES_F77_FILES, EXAMPLES_F95_FILES

_LOG = logging.getLogger(__name__)


class Tests(unittest.TestCase):

    def test_ast_generalizer(self):
        tree = typed_ast.ast3.parse("""my_file: t.IO[bytes] = None""", mode='exec')
        self.assertIsInstance(tree, typed_ast.ast3.Module)
        self.assertIsInstance(tree.body[0], typed_ast.ast3.AnnAssign)
        self.assertIsInstance(tree.body[0].annotation, typed_ast.ast3.Subscript)

    def test_new_cases(self):
        """Optional tests for exeprimental or local files."""
        paths = [
            '~/Projects/fortran/flash-subset/FLASH4.4/source/physics/Hydro/HydroMain/simpleUnsplit/HLL/hy_hllUnsplit.F90'
            '']
        for path in paths:
            path = pathlib.Path(path).expanduser()
            if not path.is_file():
                continue
            with self.subTest(path=path):
                parser = FortranParser()
                root_node = parser.parse(path, verbosity=100)
                self.assertIsNotNone(root_node)
                generalizer = FortranAstGeneralizer()
                tree = generalizer.generalize(root_node)
                self.assertIsInstance(tree, typed_ast.ast3.AST)
                typed_astunparse.dump(tree)

    def test_parse(self):
        for input_path in EXAMPLES_F77_FILES + EXAMPLES_F95_FILES:
            with self.subTest(input_path=input_path):
                parser = FortranParser()
                root_node = parser.parse(input_path, verbosity=100)
                self.assertIsNotNone(root_node)

    def test_generalize(self):
        for input_path in EXAMPLES_F77_FILES:
            with self.subTest(input_path=input_path):
                parser = FortranParser()
                root_node = parser.parse(input_path, verbosity=100)
                self.assertIsNotNone(root_node)
                generalizer = FortranAstGeneralizer()
                tree = generalizer.generalize(root_node)
                self.assertIsInstance(tree, typed_ast.ast3.AST)
                #typed_astunparse.dump(tree)
                #code = typed_astunparse.unparse(typed_tree)
                #self.assertGreater(len(code), 0)
                #result_path = transformations_path.joinpath(input_path.stem + '.py')
                #with open(result_path, 'w') as result_file:
                #    result_file.write(code)
                #_LOG.debug('```%s```', code)

    def test_unparse(self):
        for input_path in EXAMPLES_F77_FILES:
            with self.subTest(input_path=input_path):
                parser = FortranParser()
                root_node = parser.parse(input_path, verbosity=100)
                self.assertIsNotNone(root_node)
                generalizer = FortranAstGeneralizer()
                tree = generalizer.generalize(root_node)
                self.assertIsInstance(tree, typed_ast.ast3.AST)
                _LOG.debug('generalized Fortran tree %s', typed_astunparse.dump(tree))
                unparser = Fortran77Unparser()
                code = unparser.unparse(tree)
                try:
                    code = unparser.unparse(tree)
                except Exception as err:
                    raise AssertionError(typed_astunparse.dump(tree)) from err
                self.assertIsInstance(code, str)
