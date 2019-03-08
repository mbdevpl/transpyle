"""Tests of C++ language support."""

import logging
import unittest

import typed_astunparse

from transpyle.general.code_reader import CodeReader
from transpyle.cpp.parser import CppParser
from transpyle.cpp.ast_generalizer import CppAstGeneralizer

from test.common import EXAMPLES_CPP14_FILES, basic_check_cpp_ast, basic_check_python_ast

_LOG = logging.getLogger(__name__)


class Tests(unittest.TestCase):

    def test_generalize_examples(self):
        code_reader = CodeReader()
        parser = CppParser()
        for path in EXAMPLES_CPP14_FILES:
            ast_generalizer = CppAstGeneralizer(scope={'path': path})
            code = code_reader.read_file(path)
            tree = parser.parse(code, path)
            basic_check_cpp_ast(self, path, tree)
            with self.subTest(path=path):
                tree = ast_generalizer.generalize(tree)
                basic_check_python_ast(self, path, tree)
                _LOG.debug('%s', typed_astunparse.dump(tree))
                _LOG.debug('%s', typed_astunparse.unparse(tree))
