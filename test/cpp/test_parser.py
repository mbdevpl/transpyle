"""Tests of C++ parsing."""

import logging
import unittest

import timing

from transpyle.general.code_reader import CodeReader
from transpyle.cpp.parser import CppParser

from test.common import basic_check_cpp_ast, execute_on_all_language_examples

_LOG = logging.getLogger(__name__)

_TIME = timing.get_timing_group(__name__)


class Tests(unittest.TestCase):

    @execute_on_all_language_examples('cpp14')
    def test_parse_examples(self, input_path):
        code_reader = CodeReader()
        code = code_reader.read_file(input_path)
        parser = CppParser()
        with _TIME.measure('parse.{}'.format(input_path.name.replace('.', '_'))) as timer:
            cpp_ast = parser.parse(code, input_path)
        basic_check_cpp_ast(self, input_path, cpp_ast)
        _LOG.info('parsed "%s" in %fs', input_path, timer.elapsed)
