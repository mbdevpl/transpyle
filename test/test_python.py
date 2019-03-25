"""Tests of Python language support."""

import ast
import contextlib
import logging
import os
import types
import unittest

import horast
import timing
import typed_ast.ast3

from transpyle.general import CodeReader, Language, Parser
from transpyle.python import PythonAstGeneralizer
from transpyle.python.parser import \
    NativePythonParser, TypedPythonParser, TypedPythonParserWithComments
from transpyle.python.unparser import \
    NativePythonUnparser, TypedPythonUnparser, TypedPythonUnparserWithComments
from transpyle.python.transformations import inline_syntax, inline

from .common import EXAMPLES_PY3, basic_check_python_ast, execute_on_all_language_examples
from .examples_inlining import \
    buy_products, buy, buy_products_inlined, \
    just_return, return_me, just_return_inlined, \
    just_assign, just_assign_inlined, \
    print_and_get_absolute, absolute_value, print_and_get_absolute_inlined, \
    inline_oneliner, add_squares, inline_oneliner_inlined

_LOG = logging.getLogger(__name__)

_TIME = timing.get_timing_group(__name__)

PARSER_CLASSES = (NativePythonParser, TypedPythonParser, TypedPythonParserWithComments)

UNPARSER_CLASSES = (NativePythonUnparser, TypedPythonUnparser, TypedPythonUnparserWithComments)

INLINING_EXAMPLES = {
    (buy_products, buy): buy_products_inlined,
    (just_return, return_me): just_return_inlined,
    (just_assign, return_me): just_assign_inlined,
    (print_and_get_absolute, absolute_value): print_and_get_absolute_inlined,
    (inline_oneliner, add_squares): inline_oneliner_inlined}


class ParserTests(unittest.TestCase):

    def test_construct_parser(self):
        for parser_class in PARSER_CLASSES:
            with self.subTest(cls=parser_class):
                parser = parser_class()
                self.assertIsNotNone(parser)

    def test_parse(self):
        for parser_class, examples in zip(PARSER_CLASSES, EXAMPLES_PY3):
            parser = parser_class()
            for example in examples:
                with self.subTest(cls=parser_class, example=example):
                    tree = parser.parse(code=example, path=None)
                    self.assertIsNotNone(tree)


class AstGeneralizerTests(unittest.TestCase):

    def test_ast_generalizer(self):
        tree = typed_ast.ast3.parse("""my_file: t.IO[bytes] = None""", mode='exec')
        self.assertIsInstance(tree, typed_ast.ast3.Module)
        self.assertIsInstance(tree.body[0], typed_ast.ast3.AnnAssign)
        self.assertIsInstance(tree.body[0].annotation, typed_ast.ast3.Subscript)

        tree = typed_ast.ast3.parse("""my_mapping: t.Dict[int, str] = {}""", mode='exec')
        self.assertIsInstance(tree, typed_ast.ast3.Module)
        self.assertIsInstance(tree.body[0], typed_ast.ast3.AnnAssign)
        self.assertIsInstance(tree.body[0].annotation, typed_ast.ast3.Subscript)
        self.assertIsInstance(tree.body[0].annotation.slice, typed_ast.ast3.Index)

        tree = typed_ast.ast3.parse("""my_mapping: t.Dict[1:2, str] = {}""", mode='exec')
        self.assertIsInstance(tree, typed_ast.ast3.Module)
        self.assertIsInstance(tree.body[0], typed_ast.ast3.AnnAssign)
        self.assertIsInstance(tree.body[0].annotation, typed_ast.ast3.Subscript)
        self.assertIsInstance(tree.body[0].annotation.slice, typed_ast.ast3.ExtSlice)

    @execute_on_all_language_examples('python3')
    def test_generalize_examples(self, input_path):
        code_reader = CodeReader()
        code = code_reader.read_file(input_path)
        parser = TypedPythonParserWithComments()
        with _TIME.measure('parse.{}'.format(input_path.name.replace('.', '_'))) as timer:
            python_ast = parser.parse(code, input_path)
        basic_check_python_ast(self, input_path, python_ast)
        _LOG.info('parsed "%s" in %fs', input_path, timer.elapsed)

        ast_generalizer = PythonAstGeneralizer()
        with _TIME.measure('generalize.{}'.format(input_path.name.replace('.', '_'))) as timer:
            syntax = ast_generalizer.generalize(python_ast)
        basic_check_python_ast(self, input_path, syntax)
        _LOG.info('generalized "%s" in %fs', input_path, timer.elapsed)


class UnparserTests(unittest.TestCase):

    def test_construct_unparser(self):
        for unparser_class in UNPARSER_CLASSES:
            with self.subTest(cls=unparser_class):
                unparser = unparser_class()
                self.assertIsNotNone(unparser)

    def test_unparse(self):
        for unparser_class in UNPARSER_CLASSES:
            with self.subTest(cls=unparser_class):
                unparser = unparser_class()
                self.assertIsNotNone(unparser)
                if unparser_class is NativePythonUnparser:
                    ast_library = ast
                else:
                    ast_library = typed_ast.ast3
                tree = ast_library.parse('a = 1\nb = 2')
                code = unparser.unparse(tree)
                self.assertIsInstance(code, str)

    def test_roundtrip_unparse(self):
        for parser_class, unparser_class, examples in zip(
                PARSER_CLASSES, UNPARSER_CLASSES, EXAMPLES_PY3):
            parser = parser_class()
            unparser = unparser_class()
            for example in examples:
                with self.subTest(cls=parser_class, example=example):
                    tree = parser.parse(code=example, path=None)
                    new_code = unparser.unparse(tree).strip()
                    try:
                        new_tree = parser.parse(new_code, path=None)
                    except Exception as err:
                        raise AssertionError('failed to re-parse the unparsed code """{}"""'
                                             .format(new_code)) from err
                    self.assertEqual(unparser.dump(tree), unparser.dump(new_tree))
                    self.assertEqual(example, new_code)


class TransformationsTests(unittest.TestCase):

    """Testing the AST transformations."""

    def test_examples(self):
        with open(os.devnull, 'w') as devnull:
            for (target, inlined), target_inlined in INLINING_EXAMPLES.items():
                for example in (target, inlined, target_inlined):
                    with contextlib.redirect_stdout(devnull):
                        example()
            with contextlib.redirect_stdout(devnull):
                print_and_get_absolute(1)
                print_and_get_absolute_inlined(1)
                inline_oneliner(1)
                inline_oneliner_inlined(1)

    def test_inline_syntax(self):
        language = Language.find('Python 3')
        parser = Parser.find(language)()
        for (target, inlined), target_inlined in INLINING_EXAMPLES.items():
            target_code = CodeReader.read_function(target)
            inlined_code = CodeReader.read_function(inlined)
            reference_code = CodeReader.read_function(target_inlined)
            target_syntax = parser.parse(target_code).body[0]
            inlined_syntax = parser.parse(inlined_code).body[0]
            with self.subTest(target=target, inlined=inlined):
                target_inlined_syntax = inline_syntax(target_syntax, inlined_syntax, verbose=False)
                target_inlined_code = horast.unparse(target_inlined_syntax)
                _LOG.warning('%s', target_inlined_code)
                self.assertEqual(reference_code.replace('_inlined(', '(').lstrip(),
                                 target_inlined_code.lstrip())

    def test_inline(self):
        for (target, inlined), target_inlined in INLINING_EXAMPLES.items():
            with self.subTest(target=target, inlined=inlined):
                target_inlined_ = inline(target, inlined)
                self.assertIsInstance(target_inlined_, types.FunctionType)
