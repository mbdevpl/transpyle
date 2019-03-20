"""Tests of C++ language support."""

import logging
import unittest

import timing
import typed_astunparse

from transpyle.general.code_reader import CodeReader
from transpyle.cpp.parser import CppParser
from transpyle.cpp.ast_generalizer import CppAstGeneralizer

from test.common import \
    basic_check_cpp_ast, basic_check_python_ast, execute_on_all_language_examples

_LOG = logging.getLogger(__name__)

_TIME = timing.get_timing_group(__name__)


class Tests(unittest.TestCase):

    @execute_on_all_language_examples('cpp14')
    def test_generalize_examples(self, input_path):
        code_reader = CodeReader()
        code = code_reader.read_file(input_path)
        parser = CppParser()
        cpp_ast = parser.parse(code, input_path)
        basic_check_cpp_ast(self, input_path, cpp_ast)
        ast_generalizer = CppAstGeneralizer(scope={'path': input_path})
        with _TIME.measure('generalize.{}'.format(input_path.name.replace('.', '_'))) as timer:
            syntax = ast_generalizer.generalize(cpp_ast)
        basic_check_python_ast(self, input_path, syntax)
        _LOG.info('generalized "%s" in %fs', input_path, timer.elapsed)
        _LOG.debug('%s', typed_astunparse.dump(syntax))
        _LOG.debug('%s', typed_astunparse.unparse(syntax))
