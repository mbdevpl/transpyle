"""Integration tests for transpiling between different languages."""

import itertools
import sys
import unittest

from transpyle.general.code_reader import CodeReader
from transpyle.general.language import Language
from transpyle.general.parser import Parser
from transpyle.general.ast_generalizer import AstGeneralizer
from transpyle.general.unparser import Unparser
from transpyle.general.translator import Translator, AutoTranslator

from .common import EXAMPLES_LANGS_NAMES, EXAMPLES_FILES

NOT_PARSED_LANGS = ('C++14', 'Cython')

NOT_UNPARSED_LANGS = ('C11', 'C++14', 'Cython')


class Tests(unittest.TestCase):

    def test_class_finding(self):
        for language_codename, language_name in EXAMPLES_LANGS_NAMES.items():
            if language_name in NOT_UNPARSED_LANGS:
                continue
            with self.subTest(language_codename=language_codename, language_name=language_name):
                language = Language.find(language_name)
                self.assertIsInstance(language, Language)
                parser = Parser.find(language)()
                self.assertIsInstance(parser, Parser)
                ast_generalizer = AstGeneralizer.find(language)()
                self.assertIsInstance(ast_generalizer, AstGeneralizer)
                unparser = Unparser.find(language)()
                self.assertIsInstance(unparser, Unparser)

    def test_auto_translator_init(self):
        for (_, language_from_name), (_, language_to_name) \
                in itertools.product(EXAMPLES_LANGS_NAMES.items(), EXAMPLES_LANGS_NAMES.items()):
            if language_from_name in NOT_PARSED_LANGS or language_to_name in NOT_UNPARSED_LANGS:
                continue
            with self.subTest(language_from_name=language_from_name,
                              language_to_name=language_to_name):
                from_language = Language.find(language_from_name)
                self.assertIsInstance(from_language, Language)
                to_language = Language.find(language_to_name)
                self.assertIsInstance(to_language, Language)
                translator = AutoTranslator(from_language, to_language)
                self.assertIsInstance(translator, Translator)
                # transpiler = AutoTranspiler(from_language, to_language)

    @unittest.skipIf(sys.version_info[:2] < (3, 6), 'unsupported in Python < 3.6')
    def test_auto_processing(self):
        for language_codename, paths in EXAMPLES_FILES.items():
            language_name = EXAMPLES_LANGS_NAMES[language_codename]
            if language_name in NOT_PARSED_LANGS:
                continue
            language = Language.find(language_name)
            self.assertIsInstance(language, Language, msg=(language_codename, language_name))
            reader = CodeReader()
            for path in paths:
                code = reader.read_file(path)
                with self.subTest(language_name=language_name, language=language):
                    parser = Parser.find(language)()
                    specific_ast = parser.parse(code, path)
                    ast_generalizer = AstGeneralizer.find(language)()
                    general_ast = ast_generalizer.generalize(specific_ast)

    def test_language_deduction(self):
        self.skipTest('not ready yet')
