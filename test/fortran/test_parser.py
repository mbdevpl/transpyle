"""Tests for parsing of Fortran code."""

import logging
import unittest

import timing

from transpyle.fortran.parser import FortranParser

from test.common import basic_check_fortran_ast, execute_on_all_language_examples

_LOG = logging.getLogger(__name__)

_TIME = timing.get_timing_group(__name__)


class Tests(unittest.TestCase):

    @execute_on_all_language_examples('f77', 'f95')
    def test_parse_examples(self, input_path):
        parser = FortranParser()
        with _TIME.measure('parse.{}'.format(input_path.name.replace('.', '_'))) as timer:
            fortran_ast = parser.parse('', input_path)
        basic_check_fortran_ast(self, input_path, fortran_ast)
        _LOG.info('parsed "%s" in %fs', input_path, timer.elapsed)
