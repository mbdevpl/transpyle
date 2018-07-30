"""Tests of C language support."""

import logging
import unittest

from transpyle.general.code_reader import CodeReader
from transpyle.c.parser import C99Parser

from test.common import EXAMPLES_C11_FILES, basic_check_c_ast

_LOG = logging.getLogger(__name__)


class Tests(unittest.TestCase):

    def test_parse_examples(self):
        code_reader = CodeReader()
        parser = C99Parser()
        for path in EXAMPLES_C11_FILES:
            code = code_reader.read_file(path)
            tree = parser.parse(code, path)
            basic_check_c_ast(self, path, tree)
