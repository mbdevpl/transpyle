"""Integration tests for translating and transpiling between different languages."""

import itertools
import logging
import os
import pathlib
import sys
import tempfile
import unittest

import timing

from transpyle.general.code_reader import CodeReader
# from transpyle.general.code_writer import CodeWriter
from transpyle.general.language import Language
from transpyle.general.parser import Parser
from transpyle.general.ast_generalizer import AstGeneralizer
from transpyle.general.unparser import Unparser
from transpyle.general.translator import Translator, AutoTranslator
from transpyle.general.transpiler import AutoTranspiler

from transpyle.fortran.parser import FortranParser
from transpyle.fortran.ast_generalizer import FortranAstGeneralizer
from transpyle.fortran.unparser import Fortran77Unparser, Fortran2008Unparser

from transpyle.python.parser import TypedPythonParserWithComments
from transpyle.python.unparser import TypedPythonUnparserWithComments

from .common import (
    EXAMPLES_LANGS_NAMES, EXAMPLES_FILES, EXAMPLES_ROOTS,
    basic_check_cpp_code, basic_check_fortran_code, make_f2py_tmp_folder, basic_check_python_code,
    execute_on_examples, execute_on_language_fundamentals, execute_on_language_examples)

_LOG = logging.getLogger(__name__)

_TIME = timing.get_timing_group(__name__)

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


class CAndPythonTests(unittest.TestCase):

    @execute_on_language_examples('c11')
    def test_translate_c_to_python(self, input_path):
        reader = CodeReader()
        c_code = reader.read_file(input_path)
        language_from = Language.find('C11')
        language_to = Language.find('Python')
        translator = AutoTranslator(language_from, language_to)
        with _TIME.measure('translate.c11_to_python3.{}'
                           .format(input_path.name.replace('.', '_'))) as timer:
            python_code = translator.translate(c_code, input_path)
        basic_check_python_code(self, input_path, python_code)
        _LOG.info('translated "%s" to Python in %fs', input_path, timer.elapsed)


class CppAndPythonTests(unittest.TestCase):

    @execute_on_examples([
        EXAMPLES_ROOTS['python3'].joinpath(_ + '.py')
        for _ in {'fundamentals', 'do_nothing', 'compute_pi', 'gemm',
                  'simple_class', 'typical_class'}])
    def test_translate_python_to_cpp(self, input_path):
        reader = CodeReader()
        python_code = reader.read_file(input_path)
        language_from = Language.find('Python')
        language_to = Language.find('C++')
        translator = AutoTranslator(language_from, language_to)
        with _TIME.measure('translate.python3_to_cpp14.{}'
                           .format(input_path.name.replace('.', '_'))) as timer:
            cpp_code = translator.translate(python_code)
        basic_check_cpp_code(self, input_path, cpp_code)
        _LOG.info('translated "%s" to C++ in %fs', input_path, timer.elapsed)

    @execute_on_language_examples('cpp14')
    def test_translate_cpp_to_python(self, input_path):
        reader = CodeReader()
        cpp_code = reader.read_file(input_path)
        language_from = Language.find('C++')
        language_to = Language.find('Python')
        translator = AutoTranslator(language_from, language_to,
                                    ast_generalizer_kwargs={'scope': {'path': input_path}})
        python_code = translator.translate(cpp_code, input_path)
        basic_check_python_code(self, input_path, python_code)


class FortranAndPythonTests(unittest.TestCase):

    @execute_on_language_examples('f77', 'f95')
    def test_translate_fortran_to_python(self, input_path):
        reader = CodeReader()
        code = reader.read_file(input_path)
        parser = FortranParser()
        fortran_ast = parser.parse(code, input_path)
        generalizer = FortranAstGeneralizer()
        syntax = generalizer.generalize(fortran_ast)
        unparser = TypedPythonUnparserWithComments()
        python_code = unparser.unparse(syntax)
        basic_check_python_code(self, input_path, python_code)

    @execute_on_language_fundamentals('python3')
    def test_translate_python_to_fortran(self, input_path):
        reader = CodeReader()
        python_code = reader.read_file(input_path)
        parser = TypedPythonParserWithComments(default_mode='exec')
        tree = parser.parse(python_code, input_path)
        unparser = Fortran77Unparser()
        fortran_code = unparser.unparse(tree)
        basic_check_fortran_code(self, input_path, fortran_code)

    @unittest.skipIf(sys.version_info[:2] < (3, 6), 'requires Python >= 3.6')
    @unittest.skipUnless(os.environ.get('TEST_LONG'), 'skipping long test')
    @execute_on_language_examples('f77', 'f95')
    def test_translate_fortran_to_python_to_fortran(self, input_path):
        parser = FortranParser()
        fortran_ast = parser.parse('', input_path)
        generalizer = FortranAstGeneralizer()
        syntax = generalizer.generalize(fortran_ast)
        python_unparser = TypedPythonUnparserWithComments()
        python_code = python_unparser.unparse(syntax)

        python_parser = TypedPythonParserWithComments(default_mode='exec')
        reparsed_syntax = python_parser.parse(python_code)
        fortran_unparser = Fortran77Unparser() if input_path.suffix == '.f' \
            else Fortran2008Unparser()
        fortran_code = fortran_unparser.unparse(reparsed_syntax)
        basic_check_fortran_code(self, input_path, fortran_code, suffix='.py' + input_path.suffix)

    @execute_on_examples([_ for _ in EXAMPLES_FILES['python3'] if '_openmp' in _.name])
    def test_transpile_with_openmp(self, input_path):
        output_dir = make_f2py_tmp_folder(input_path)

        transpiler = AutoTranspiler(Language.find('Python'), Language.find('Fortran'))
        self.assertIsNotNone(transpiler)
        reader = CodeReader()

        with tempfile.NamedTemporaryFile(suffix='.f90', delete=False) as output_file:
            # TODO: this leaves garbage behind in /tmp/ but is neeeded
            # by subsequent transpiler passes

            # code_writer = CodeWriter('.py')
            # target_inlined_path = pathlib.Path(output_file.name)
            # code_writer.write_file(target_inlined_code, target_inlined_path)
            output_path = pathlib.Path(output_file.name)

        compiled_path = transpiler.transpile(
            reader.read_file(input_path), input_path, output_path, output_dir)
        # TODO: run it
