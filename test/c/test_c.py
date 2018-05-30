"""Tests of C language support."""

import logging
import unittest

import typed_astunparse

from transpyle.general.code_reader import CodeReader
from transpyle.c.parser import C99Parser
from transpyle.c.ast_generalizer import CAstGeneralizer
from .examples import EXAMPLES_C11_FILES, basic_check_c_ast, basic_check_python_ast

_LOG = logging.getLogger(__name__)


class Tests(unittest.TestCase):

    def test_parse_examples(self):
        code_reader = CodeReader()
        parser = C99Parser()
        for path in EXAMPLES_C11_FILES:
            code = code_reader.read_file(path)
            tree = parser.parse(code, path)
            basic_check_c_ast(self, path, tree)

    def test_generalize_examples(self):
        code_reader = CodeReader()
        parser = C99Parser()
        ast_generalizer = CAstGeneralizer()
        for path in EXAMPLES_C11_FILES:
            code = code_reader.read_file(path)
            tree = parser.parse(code, path)
            basic_check_c_ast(self, path, tree)
            tree = ast_generalizer.generalize(tree)
            basic_check_python_ast(self, path, tree)
            _LOG.debug('%s', typed_astunparse.dump(tree))
            _LOG.debug('%s', typed_astunparse.unparse(tree))
