"""Tests of C++ parsing."""

# import logging
import unittest

from transpyle.general.code_reader import CodeReader
from transpyle.cpp.parser import CppParser
from ..examples import EXAMPLES_CPP14_FILES, basic_check_cpp_ast

# _LOG = logging.getLogger(__name__)


class Tests(unittest.TestCase):

    def test_parse_examples(self):
        code_reader = CodeReader()
        parser = CppParser()
        for path in EXAMPLES_CPP14_FILES:
            code = code_reader.read_file(path)
            tree = parser.parse(code, path)
            basic_check_cpp_ast(self, path, tree)
