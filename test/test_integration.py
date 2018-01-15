"""Integration tests for transpiling between different languages."""

import itertools
import pathlib
import sys
import unittest

from transpyle.general.code_reader import CodeReader
from transpyle.general.code_writer import CodeWriter
from transpyle.general.language import Language
from transpyle.general.parser import Parser
from transpyle.general.ast_generalizer import AstGeneralizer
from transpyle.general.unparser import Unparser
from transpyle.general.translator import Translator, AutoTranslator
# from transpyle.general.transpiler import AutoTranspiler

from transpyle.fortran.parser import FortranParser
from transpyle.fortran.ast_generalizer import FortranAstGeneralizer
from transpyle.fortran.unparser import Fortran77Unparser

from transpyle.python.parser import TypedPythonParserWithComments
from transpyle.python.unparser import TypedPythonUnparserWithComments

from .examples import EXAMPLES_LANGS_NAMES, EXAMPLES_FILES, EXAMPLES_C11_FILES, \
    EXAMPLES_F77_FILES, EXAMPLES_PY3_FILES, basic_check_python_code


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

    def test_auto_translator_initialization(self):
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

    def test_fortran_to_python(self):
        for input_path in EXAMPLES_F77_FILES:
            parser = FortranParser()
            generalizer = FortranAstGeneralizer()
            unparser = TypedPythonUnparserWithComments()
            writer = CodeWriter('.py')
            with self.subTest(input_path=input_path):
                fortran_ast = parser.parse('', input_path)
                tree = generalizer.generalize(fortran_ast)
                python_code = unparser.unparse(tree)
                writer.write_file(python_code, pathlib.Path('/tmp', input_path.name + '.py'))

    @unittest.skip('not ready yet')
    def test_python_to_fortran(self):
        for input_path in EXAMPLES_PY3_FILES:
            reader = CodeReader()
            parser = TypedPythonParserWithComments()
            unparser = Fortran77Unparser()
            writer = CodeWriter('.f')
            with self.subTest(input_path=input_path):
                python_code = reader.read_file(input_path)
                tree = parser.parse(python_code, input_path, mode='exec')
                fortran_code = unparser.unparse(tree)
                writer.write_file(fortran_code, pathlib.Path('/tmp', input_path.name + '.f'))

    @unittest.skipIf(sys.version_info[:2] < (3, 6), 'requires Python >= 3.6')
    def test_fortran_to_python_to_fortran(self):
        for input_path in EXAMPLES_F77_FILES:
            parser = FortranParser()
            generalizer = FortranAstGeneralizer()
            unparser = TypedPythonUnparserWithComments()
            python_parser = TypedPythonParserWithComments(default_mode='exec')
            writer = CodeWriter('.f')
            with self.subTest(input_path=input_path):
                fortran_ast = parser.parse('', input_path)
                tree = generalizer.generalize(fortran_ast)
                python_code = unparser.unparse(tree)
                tree = python_parser.parse(python_code)
                fortran_code = unparser.unparse(tree)
                writer.write_file(fortran_code, pathlib.Path('/tmp', input_path.name + '.py.f'))
