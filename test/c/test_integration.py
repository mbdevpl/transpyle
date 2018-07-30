"""Integration tests for translating between C and other languages."""

import unittest

from transpyle.general.code_reader import CodeReader
from transpyle.general.language import Language
from transpyle.general.parser import Parser
from transpyle.general.ast_generalizer import AstGeneralizer
from transpyle.general.unparser import Unparser

from test.common import EXAMPLES_C11_FILES, basic_check_python_code


class Tests(unittest.TestCase):

    def test_c_to_python(self):
        language = Language.find('C11')
        python_language = Language.find('Python')
        reader = CodeReader()
        parser = Parser.find(language)()
        ast_generalizer = AstGeneralizer.find(language)()
        unparser = Unparser.find(python_language)()
        for input_path in EXAMPLES_C11_FILES:
            with self.subTest(input_path=input_path):
                code = reader.read_file(input_path)
                c_ast = parser.parse(code, input_path)
                tree = ast_generalizer.generalize(c_ast)
                python_code = unparser.unparse(tree)
                basic_check_python_code(self, input_path, python_code)
