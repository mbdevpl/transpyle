"""Tests of C++ language support."""

import logging
import os
import pathlib
import platform
import types
import unittest

import timing
import typed_astunparse

from transpyle.general.code_reader import CodeReader
from transpyle.general.binder import Binder
from transpyle.cpp.parser import CppParser
from transpyle.cpp.ast_generalizer import CppAstGeneralizer
from transpyle.cpp.unparser import Cpp14Unparser
from transpyle.cpp.compiler import CppCompilerInterface, CppSwigCompiler

from .common import \
    EXAMPLES_CPP14_FILES, basic_check_cpp_code, basic_check_cpp_ast, make_swig_tmp_folder, \
    basic_check_python_ast, execute_on_all_language_examples

_LOG = logging.getLogger(__name__)

_TIME = timing.get_timing_group(__name__)


class ParserTests(unittest.TestCase):

    @execute_on_all_language_examples('cpp14')
    def test_parse_examples(self, input_path):
        code_reader = CodeReader()
        code = code_reader.read_file(input_path)
        parser = CppParser()
        with _TIME.measure('parse.{}'.format(input_path.name.replace('.', '_'))) as timer:
            cpp_ast = parser.parse(code, input_path)
        basic_check_cpp_ast(self, input_path, cpp_ast)
        _LOG.info('parsed "%s" in %fs', input_path, timer.elapsed)


class AstGeneralizerTests(unittest.TestCase):

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


class UnparserTests(unittest.TestCase):

    @execute_on_all_language_examples('cpp14')
    def test_unparse_examples(self, input_path):
        code_reader = CodeReader()
        code = code_reader.read_file(input_path)
        parser = CppParser()
        cpp_ast = parser.parse(code, input_path)
        basic_check_cpp_ast(self, input_path, cpp_ast)
        generalizer = CppAstGeneralizer(scope={'path': input_path})
        syntax = generalizer.generalize(cpp_ast)
        basic_check_python_ast(self, input_path, syntax)

        unparser = Cpp14Unparser()
        with _TIME.measure('unparse.{}'.format(input_path.name.replace('.', '_'))) as timer:
            code = unparser.unparse(syntax)
        basic_check_cpp_code(self, input_path, code)
        _LOG.info('unparsed "%s" in %fs', input_path, timer.elapsed)

        header_unparser = Cpp14Unparser(headers=True)
        with _TIME.measure('unparse.{}.headers'.format(input_path.name.replace('.', '_'))) as timer:
            code = header_unparser.unparse(syntax)
        basic_check_cpp_code(self, input_path, code, suffix='.hpp')
        _LOG.info('unparsed "%s" in %fs', input_path, timer.elapsed)


class CompilerTests(unittest.TestCase):

    def test_cpp_paths_exist(self):
        compiler = CppCompilerInterface()
        for path in compiler.include_paths:
            self.assertTrue(path.is_dir())
        for path in compiler.library_paths:
            self.assertTrue(path.is_dir())

    @unittest.skipUnless(platform.system() == 'Linux', 'tested only on Linux')
    @unittest.skipUnless(os.environ.get('TEST_LONG'), 'skipping long test')
    @execute_on_all_language_examples('cpp14')
    def test_compile_and_bind_examples(self, input_path):
        output_dir = make_swig_tmp_folder(input_path)

        code_reader = CodeReader()
        code = code_reader.read_file(input_path)
        compiler = CppSwigCompiler()
        with _TIME.measure('compile.{}'.format(input_path.name.replace('.', '_'))) as timer:
            output_path = compiler.compile(code, input_path, output_dir)
        self.assertIsInstance(output_path, pathlib.Path)
        binder = Binder()
        with binder.temporarily_bind(output_path) as binding:
            self.assertIsInstance(binding, types.ModuleType)
        _LOG.warning('compiled "%s" in %fs', input_path, timer.elapsed)

        output_path.unlink()
        try:
            output_dir.rmdir()
        except OSError:
            pass

    def test_openmp(self):
        compiler = CppSwigCompiler()
        for input_path in EXAMPLES_CPP14_FILES:
            if input_path.name == 'matmul_openmp.cpp':
                break

        output_dir = make_swig_tmp_folder(input_path)
        with input_path.open() as input_file:
            code = input_file.read()
        output_path = compiler.compile(code, input_path, output_dir)
        self.assertIsInstance(output_path, pathlib.Path)
        binder = Binder()
        with binder.temporarily_bind(output_path) as binding:
            print(type(binding.multiply_martices_example))
            # print(help(binding.main))
            with _TIME.measure('matmul') as timer:
                ret_val = binding.multiply_martices_example(1, 3000, 3000)
            self.assertEqual(ret_val, 0)
            _LOG.warning('%s', _TIME.summary)
            self.assertIsNotNone(binding)
        output_path.unlink()
        try:
            output_dir.rmdir()
        except OSError:
            pass
