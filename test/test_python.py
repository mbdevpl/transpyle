"""Unit tests for transpyle.python package."""

import ast
import unittest

import typed_ast.ast3

from transpyle.python.parser import \
    NativePythonParser, TypedPythonParser, TypedPythonParserWithComments
from transpyle.python.unparser import \
    NativePythonUnparser, TypedPythonUnparser, TypedPythonUnparserWithComments
from .examples import EXAMPLES_PY3

PARSER_CLASSES = (NativePythonParser, TypedPythonParser, TypedPythonParserWithComments)

UNPARSER_CLASSES = (NativePythonUnparser, TypedPythonUnparser, TypedPythonUnparserWithComments)


class Tests(unittest.TestCase):

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

    def test_parse_unparse(self):
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
