"""Testing the AST transformations."""

import contextlib
import logging
import os
import types
import unittest

import horast
import typed_astunparse
import static_typing as st

from transpyle.general import CodeReader, Language, Parser
from transpyle.python.transformations import inline_syntax, inline

from .examples_inlining import \
    buy_products, buy, buy_products_inlined, \
    just_return, return_me, just_return_inlined, \
    just_assign, just_assign_inlined, \
    print_and_get_absolute, absolute_value, print_and_get_absolute_inlined, \
    inline_oneliner, add_squares, inline_oneliner_inlined

_LOG = logging.getLogger(__name__)

INLINING_EXAMPLES = {
    (buy_products, buy): buy_products_inlined,
    (just_return, return_me): just_return_inlined,
    (just_assign, return_me): just_assign_inlined,
    (print_and_get_absolute, absolute_value): print_and_get_absolute_inlined,
    (inline_oneliner, add_squares): inline_oneliner_inlined}


class Tests(unittest.TestCase):

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
