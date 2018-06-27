"""Integration tests for translating between C++ and other languages."""

import sys
import unittest

from transpyle.general.code_reader import CodeReader
from transpyle.general.language import Language
from transpyle.general.translator import AutoTranslator

from test.examples import EXAMPLES_PY3_FILES, basic_check_cpp_code


class Tests(unittest.TestCase):

    @unittest.skipIf(sys.version_info[:2] < (3, 6), 'unsupported in Python < 3.6')
    def test_python_to_cpp(self):
        language_from = Language.find('Python')
        language_to = Language.find('C++')
        reader = CodeReader()
        # parser = Parser.find(language_from)()
        # ast_generalizer = AstGeneralizer.find(language_from)()
        # unparser = Unparser.find(python_language)()
        # writer = CodeWriter('.py')
        for input_path in EXAMPLES_PY3_FILES:
            if input_path.name in {'matmul.py'}:
                continue
            translator = AutoTranslator(language_from, language_to)
            with self.subTest(input_path=input_path):
                python_code = reader.read_file(input_path)
                cpp_code = translator.translate(python_code)
                basic_check_cpp_code(self, input_path, cpp_code)
