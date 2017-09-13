"""Tests for Fortran language support."""

import logging
import pathlib
import unittest

import typed_ast.ast3
import typed_astunparse

from transpyle.general.code_writer import CodeWriter
from transpyle.fortran.parser import FortranParser
from transpyle.fortran.ast_generalizer import FortranAstGeneralizer
from transpyle.fortran.unparser import Fortran77Unparser
from .examples import EXAMPLES_F77_FILES, EXAMPLES_F95_FILES, TRANSFORMATIONS_ROOT

_LOG = logging.getLogger(__name__)


class Tests(unittest.TestCase):

    def test_ast_generalizer(self):
        tree = typed_ast.ast3.parse("""my_file: t.IO[bytes] = None""", mode='exec')
        self.assertIsInstance(tree, typed_ast.ast3.Module)
        self.assertIsInstance(tree.body[0], typed_ast.ast3.AnnAssign)
        self.assertIsInstance(tree.body[0].annotation, typed_ast.ast3.Subscript)

        tree = typed_ast.ast3.parse("""my_mapping: t.Dict[int, str] = {}""", mode='exec')
        self.assertIsInstance(tree, typed_ast.ast3.Module)
        self.assertIsInstance(tree.body[0], typed_ast.ast3.AnnAssign)
        self.assertIsInstance(tree.body[0].annotation, typed_ast.ast3.Subscript)
        self.assertIsInstance(tree.body[0].annotation.slice, typed_ast.ast3.Index)

        tree = typed_ast.ast3.parse("""my_mapping: t.Dict[1:2, str] = {}""", mode='exec')
        self.assertIsInstance(tree, typed_ast.ast3.Module)
        self.assertIsInstance(tree.body[0], typed_ast.ast3.AnnAssign)
        self.assertIsInstance(tree.body[0].annotation, typed_ast.ast3.Subscript)
        self.assertIsInstance(tree.body[0].annotation.slice, typed_ast.ast3.ExtSlice)


    def test_new_cases(self):
        """Optional tests for exeprimental or local files."""
        paths = [
            '~/Projects/fortran/flash-subset/FLASH4.4/source/physics/Hydro/HydroMain/simpleUnsplit/HLL/hy_hllUnsplit.F90'
            '']
        parser = FortranParser()
        generalizer = FortranAstGeneralizer()
        for path in paths:
            path = pathlib.Path(path).expanduser()
            if not path.is_file():
                continue
            with self.subTest(path=path):
                root_node = parser.parse(path, verbosity=100)
                self.assertIsNotNone(root_node)
                tree = generalizer.generalize(root_node)
                self.assertIsInstance(tree, typed_ast.ast3.AST)
                _LOG.debug('%s', typed_astunparse.dump(tree))
                with open(TRANSFORMATIONS_ROOT.joinpath(path.name + '-ast.py'), 'w') as result_file:
                    result_file.write(typed_astunparse.dump(tree))

    def test_parse(self):
        parser = FortranParser()
        for input_path in EXAMPLES_F77_FILES + EXAMPLES_F95_FILES:
            with self.subTest(input_path=input_path):
                root_node = parser.parse(input_path, verbosity=100)
                self.assertIsNotNone(root_node)

    def test_generalize(self):
        parser = FortranParser()
        generalizer = FortranAstGeneralizer()
        for input_path in EXAMPLES_F77_FILES + EXAMPLES_F95_FILES:
            with self.subTest(input_path=input_path):
                tree = generalizer.generalize(parser.parse(input_path, verbosity=100))
                self.assertIsInstance(tree, typed_ast.ast3.AST)
                with open(TRANSFORMATIONS_ROOT.joinpath(input_path.name + '-ast.py'), 'w') as result_file:
                    result_file.write(typed_astunparse.dump(tree))

    def test_unparse(self):
        parser = FortranParser()
        generalizer = FortranAstGeneralizer()
        unparser = Fortran77Unparser()
        writer = CodeWriter('.f')
        for input_path in EXAMPLES_F77_FILES + EXAMPLES_F95_FILES:
            with self.subTest(input_path=input_path):
                tree = generalizer.generalize(parser.parse(input_path, verbosity=100))
                self.assertIsInstance(tree, typed_ast.ast3.AST)
                _LOG.debug('generalized Fortran tree %s', typed_astunparse.dump(tree))
                code = unparser.unparse(tree)
                self.assertIsInstance(code, str)
                writer.write_file(code, TRANSFORMATIONS_ROOT.joinpath(input_path.name + '.f'))
