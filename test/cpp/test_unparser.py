"""Tests for C++ unparsing."""

import logging
import unittest

import timing

from transpyle.general.code_reader import CodeReader
from transpyle.cpp.parser import CppParser
from transpyle.cpp.ast_generalizer import CppAstGeneralizer
from transpyle.cpp.unparser import Cpp14Unparser

from test.common import \
    basic_check_cpp_code, basic_check_cpp_ast, basic_check_python_ast, \
    execute_on_all_language_examples

_LOG = logging.getLogger(__name__)

_TIME = timing.get_timing_group(__name__)


class Tests(unittest.TestCase):

    @execute_on_all_language_examples('cpp14')
    def test_unparse_examples(self, input_path):
        code_reader = CodeReader()
        code = code_reader.read_file(input_path)
        parser = CppParser()
        cpp_ast = parser.parse(code, input_path)
        basic_check_cpp_ast(self, input_path, cpp_ast)
        generalizer = CppAstGeneralizer(scope={'path': input_path})
        syntax = generalizer.generalize(cpp_ast)
        basic_check_python_ast(self, input_path, syntax)

        unparser = Cpp14Unparser()
        with _TIME.measure('unparse.{}'.format(input_path.name.replace('.', '_'))) as timer:
            code = unparser.unparse(syntax)
        basic_check_cpp_code(self, input_path, code)
        _LOG.info('unparsed "%s" in %fs', input_path, timer.elapsed)

        header_unparser = Cpp14Unparser(headers=True)
        with _TIME.measure('unparse.{}.headers'.format(input_path.name.replace('.', '_'))) as timer:
            code = header_unparser.unparse(syntax)
        basic_check_cpp_code(self, input_path, code, suffix='.hpp')
        _LOG.info('unparsed "%s" in %fs', input_path, timer.elapsed)
