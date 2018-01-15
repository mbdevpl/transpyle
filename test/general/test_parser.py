"""Unit tests for Parser class."""

import textwrap
import unittest

from transpyle.general.parser import validate_indentation, Parser

CASES = {
    '   a\n   b\n   c': 'a\nb\nc',
    '    ': '',
    '    \n': '\n',
    '  a\n\n  b': 'a\n\nb',
    '  a\n  b\n': 'a\nb\n',
    '\tx\n\t\ty\n\tz': 'x\n\ty\nz',
    '\tx\n\t\ty\n\tz\n': 'x\n\ty\nz\n'}

TYPE_ERROR_CASES = (
    12345, None)
VALUE_ERROR_CASES = (
    '\t\ttabs\n    spaces', '    spaces\n\t\ttabs', '\t tab and spaces\n\t on both lines',
    '\t\t\n\n    ')


class Tests(unittest.TestCase):

    def test_validate_indentation(self):
        for case in TYPE_ERROR_CASES:
            with self.assertRaises(TypeError, msg=repr(case)):
                validate_indentation(case)
        for case in VALUE_ERROR_CASES:
            with self.assertRaises(ValueError, msg=repr(case)):
                validate_indentation(case)
        for case in CASES:
            validate_indentation(case)

    def test_dedent_code(self):
        for case, result in CASES.items():
            self.assertEqual(textwrap.dedent(case), result, msg=(repr(case), repr(result)))

    def test_parser_is_abstract(self):
        parser = Parser()
        with self.assertRaises(NotImplementedError):
            parser.parse('code')

    def test_parser_parse(self):
        class MyParser(Parser):  # pylint: disable=abstract-method
            def _parse_scope(self, code, path=None):
                return code
        parser = MyParser()
        with self.assertRaises(NotImplementedError):
            parser.parse('1\n2\n3\n4\n', scopes=[(0, 1), (2, 3)])
        for case, result in CASES.items():
            self.assertEqual(parser.parse(case), result, msg=(repr(case), repr(result)))
            self.assertEqual(parser.parse(case, dedent=False), case, msg=repr(case))

    def test_parser_parse_single_scope(self):
        class MyParser(Parser):  # pylint: disable=abstract-method
            def _parse_scope(self, code, path=None):
                return code
        parser = MyParser()
        self.assertEqual(parser.parse('1\n2\n3\n4\n', scopes=[(1, 2)]), '2\n')
        self.assertEqual(parser.parse('1\n2\n3\n4\n', scopes=[(2, None)]), '3\n4\n')
        parser = MyParser(default_scopes=[(1, 2)])
        self.assertEqual(parser.parse('1\n2\n3\n4\n'), '2\n')

    def test_parser_parse_many_scopes(self):
        class MyParser(Parser):
            def _parse_scope(self, code, path=None):
                return code

            def _join_scopes(self, parsed_scopes):
                return ''.join(parsed_scopes)
        parser = MyParser()
        self.assertEqual(parser.parse('1\n2\n3\n4\n', scopes=[(0, 1), (2, 3)]), '1\n3\n')
