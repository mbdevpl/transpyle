"""Tests for Fortran language support."""

import logging
import unittest

import timing

from transpyle.fortran.parser import FortranParser
from transpyle.fortran.ast_generalizer import FortranAstGeneralizer
from transpyle.fortran.unparser import Fortran77Unparser

from test.common import \
    basic_check_fortran_code, basic_check_fortran_ast, basic_check_python_ast, \
    execute_on_all_language_fundamentals

_LOG = logging.getLogger(__name__)

_TIME = timing.get_timing_group(__name__)


class Tests(unittest.TestCase):

    @execute_on_all_language_fundamentals('f77', 'f95')
    def test_unparse_fundamentals(self, input_path):
        parser = FortranParser()
        fortran_ast = parser.parse('', input_path)
        basic_check_fortran_ast(self, input_path, fortran_ast)
        generalizer = FortranAstGeneralizer()
        syntax = generalizer.generalize(fortran_ast)
        basic_check_python_ast(self, input_path, syntax)
        unparser = Fortran77Unparser()
        with _TIME.measure('unparse.{}'.format(input_path.name.replace('.', '_'))) as timer:
            code = unparser.unparse(syntax)
        basic_check_fortran_code(self, input_path, code)
        _LOG.info('unparsed "%s" in %fs', input_path, timer.elapsed)
