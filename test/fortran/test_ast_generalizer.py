"""Tests for generalizing of Fortran code into Python AST."""

import logging
import unittest

import timing

from transpyle.fortran.parser import FortranParser
from transpyle.fortran.ast_generalizer import FortranAstGeneralizer

from test.common import \
    basic_check_fortran_ast, basic_check_python_ast, execute_on_all_language_examples

_LOG = logging.getLogger(__name__)

_TIME = timing.get_timing_group(__name__)


class Tests(unittest.TestCase):

    @execute_on_all_language_examples('f77', 'f95')
    def test_generalize_examples(self, input_path):
        parser = FortranParser()
        fortran_ast = parser.parse('', input_path)
        basic_check_fortran_ast(self, input_path, fortran_ast)
        generalizer = FortranAstGeneralizer()
        with _TIME.measure('generalize.{}'.format(input_path.name.replace('.', '_'))) as timer:
            syntax = generalizer.generalize(fortran_ast)
        basic_check_python_ast(self, input_path, syntax)
        _LOG.info('generalized "%s" in %fs', input_path, timer.elapsed)
