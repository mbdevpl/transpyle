"""Integration tests based on various scientific applications."""

#import logging
import pathlib
import unittest

from transpyle.fortran.parser import FortranParser
from transpyle.fortran.ast_generalizer import FortranAstGeneralizer
from transpyle.fortran.unparser import Fortran77Unparser, Fortran2008Unparser
from transpyle.python.parser import TypedPythonParserWithComments
from transpyle.python.unparser import TypedPythonUnparserWithComments
from .examples import \
    APPS_RESULTS_ROOT, basic_check_fortran_code, basic_check_fortran_ast, \
    basic_check_python_code, basic_check_python_ast

#_LOG = logging.getLogger(__name__)


class Tests(unittest.TestCase):

    @unittest.skip('not ready yet')
    def test_roundrtip_miranda_io(self):
        results_path = pathlib.Path(APPS_RESULTS_ROOT, 'miranda_io')
        results_path.mkdir(exist_ok=True)
        path = pathlib.Path('../miranda_io/miranda_io.f90').expanduser()
        if not path.is_file():
            self.skipTest('miranda_io file not present')
        fortran_parser = FortranParser()
        fortran_generalizer = FortranAstGeneralizer()
        python_unparser = TypedPythonUnparserWithComments()
        python_parser = TypedPythonParserWithComments()
        fortran_unparser = Fortran77Unparser()
        fortran_ast = fortran_parser.parse('', path)
        basic_check_fortran_ast(self, path, fortran_ast, results=results_path)
        tree = fortran_generalizer.generalize(fortran_ast)
        basic_check_python_ast(self, path, tree, results=results_path)
        python_code = python_unparser.unparse(tree)
        basic_check_python_code(self, path, python_code, results=results_path)
        tree = python_parser.parse(python_code)
        basic_check_python_ast(self, path, tree, results=results_path)
        fortran_code = fortran_unparser.unparse(tree)
        basic_check_fortran_code(self, path, fortran_code, results=results_path)

    def test_roundtrip_flash(self):
        results_path = pathlib.Path(APPS_RESULTS_ROOT, 'flash')
        results_path.mkdir(exist_ok=True)
        root_path = pathlib.Path('~/Projects/fortran/flash-subset').expanduser()
        paths = [
            'FLASH4.4/source/physics/Hydro/HydroMain/simpleUnsplit/HLL/hy_hllUnsplit.F90']
        parser = FortranParser()
        generalizer = FortranAstGeneralizer()
        python_unparser = TypedPythonUnparserWithComments()
        unparser = Fortran2008Unparser()
        for path in paths:
            path = pathlib.Path(root_path, path)
            if not path.is_file():
                continue
            with open(path) as original_file:
                basic_check_fortran_code(self, path, original_file.read(), results=results_path,
                                         append_suffix=False)
            with self.subTest(path=path):
                fortran_ast = parser.parse(None, path)
                basic_check_fortran_ast(self, path, fortran_ast, results=results_path)
                tree = generalizer.generalize(fortran_ast)
                basic_check_python_ast(self, path, tree, results=results_path)
                python_code = python_unparser.unparse(tree)
                basic_check_python_code(self, path, python_code, results=results_path)
                fortran_code = unparser.unparse(tree)
                basic_check_fortran_code(self, path, fortran_code, results=results_path)

    @unittest.skip('not ready yet')
    def test_migrate_ffb_mini_to_python(self):
        """From https://github.com/fiber-miniapp/ffb-mini"""
        results_path = pathlib.Path(APPS_RESULTS_ROOT, 'ffb-mini')
        results_path.mkdir(exist_ok=True)
        root_path = pathlib.Path('~/Projects/fortran/ffb-mini').expanduser()
        paths = [
            'src/makemesh.f90']
        parser = FortranParser()
        generalizer = FortranAstGeneralizer()
        unparser = TypedPythonUnparserWithComments()
        for path in paths:
            path = pathlib.Path(root_path, path)
            if not path.is_file():
                continue
            with self.subTest(path=path):
                #logger_level = logging.getLogger('open_fortran_parser.parser_wrapper').level
                #logging.getLogger('open_fortran_parser.parser_wrapper').setLevel(logging.CRITICAL)
                fortran_ast = parser.parse('', path)
                basic_check_fortran_ast(self, path, fortran_ast, results=results_path)
                tree = generalizer.generalize(fortran_ast)
                basic_check_python_ast(self, path, tree, results=results_path)
                python_code = unparser.unparse(tree)
                basic_check_python_code(self, path, python_code, results=results_path)
                #logging.getLogger('open_fortran_parser.parser_wrapper').setLevel(logger_level)
                #_LOG.debug('```%s```', code)
