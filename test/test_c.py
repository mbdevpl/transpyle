"""Tests of C language support."""

import logging
import unittest

import timing
import typed_astunparse

from transpyle.general.code_reader import CodeReader
from transpyle.c.parser import C99Parser
from transpyle.c.ast_generalizer import CAstGeneralizer

from .common import basic_check_c_ast, basic_check_python_ast, execute_on_language_examples

_LOG = logging.getLogger(__name__)

_TIME = timing.get_timing_group(__name__)


class ParserTests(unittest.TestCase):

    @execute_on_language_examples('c11')
    def test_parse_examples(self, input_path):
        code_reader = CodeReader()
        code = code_reader.read_file(input_path)
        parser = C99Parser()
        with _TIME.measure('parse.{}'.format(input_path.name.replace('.', '_'))) as timer:
            c_ast = parser.parse(code, input_path)
        basic_check_c_ast(self, input_path, c_ast)
        _LOG.info('parsed "%s" in %fs', input_path, timer.elapsed)


class AstGeneralizerTests(unittest.TestCase):

    @execute_on_language_examples('c11')
    def test_generalize_examples(self, input_path):
        code_reader = CodeReader()
        code = code_reader.read_file(input_path)
        parser = C99Parser()
        c_ast = parser.parse(code, input_path)
        basic_check_c_ast(self, input_path, c_ast)
        ast_generalizer = CAstGeneralizer()
        with _TIME.measure('generalize.{}'.format(input_path.name.replace('.', '_'))) as timer:
            syntax = ast_generalizer.generalize(c_ast)
        basic_check_python_ast(self, input_path, syntax)
        _LOG.info('generalized "%s" in %fs', input_path, timer.elapsed)
        _LOG.debug('%s', typed_astunparse.dump(syntax))
        _LOG.debug('%s', typed_astunparse.unparse(syntax))
