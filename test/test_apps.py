"""Integration tests based on various scientific applications."""

# import logging
import os
import pathlib
import unittest

from transpyle.general import Language, Parser, AstGeneralizer, Unparser
from .examples import \
    APPS_RESULTS_ROOT, basic_check_fortran_code, basic_check_fortran_ast, \
    basic_check_python_code, basic_check_python_ast

# _LOG = logging.getLogger(__name__)

_HERE = pathlib.Path(__file__).resolve().parent

_APPS_PARENT_PATHS = {
    'miranda_io': pathlib.Path('fortran'),
    'FLASH': pathlib.Path('fortran'),
    'FFB-MINI': pathlib.Path('fortran')}

_APPS_ROOT_PATHS = {
    'miranda_io': pathlib.Path('miranda_io'),
    'FLASH': pathlib.Path('flash-subset', 'FLASH4.4'),
    'FFB-MINI': pathlib.Path('ffb-mini')}

_APPS_OPTIONAL = {'FLASH'}

_APPS_ROOT_PATHS = {
    app: (pathlib.Path('..', path) if _HERE.parent.joinpath('..', path).is_dir()
          else pathlib.Path('..', '..', _APPS_PARENT_PATHS[app], path))
    for app, path in _APPS_ROOT_PATHS.items()}

_APPS_ROOT_PATHS = {
    app: _HERE.parent.joinpath(path).resolve() for app, path in _APPS_ROOT_PATHS.items()
    if app not in _APPS_OPTIONAL or _HERE.parent.joinpath(path).is_dir()}

_APPS_CODE_FILEPATHS = {
    'miranda_io': [pathlib.Path(_APPS_ROOT_PATHS['miranda_io'], 'miranda_io.f90')],
    'FLASH': [pathlib.Path(_APPS_ROOT_PATHS['FLASH'], 'source', pathlib.Path(input_path))
              for input_path in [
                  'physics/Hydro/HydroMain/simpleUnsplit/HLL/hy_hllUnsplit.F90'
                  ]] if 'FLASH' in _APPS_ROOT_PATHS else [],
    'FFB-MINI': [pathlib.Path(root, name)
                 for root, _, files in os.walk(str(
                     pathlib.Path(_APPS_ROOT_PATHS['FFB-MINI'], 'src')))
                 for name in files
                 if pathlib.Path(name).suffix in ('.f', '.F', '.f90') and name not in (
                     'bcgs3x.F', 'bcgsxe.F', 'calax3.F', 'callap.F', 'ddcom4.F', 'dd_mpi.F',
                     'e2plst.F', 'extrfn.F', 'gfutil.f', 'grad3x.F', 'les3x.F', 'lesrop.F',
                     'lesrpx.F', 'lessfx.F', 'lrfnms.F', 'miniapp_util.F', 'mfname.F', 'neibr2.F',
                     'nodlex.F', 'pres3e.F', 'rcmelm.F', 'reordr.F', 'rfname.F', 'srfexx.F',
                     'vel3d1.F', 'vel3d2.F')]}


def _prepare_roundtrip(case, language: Language):
    parser = Parser.find(language)()
    case.assertIsInstance(parser, Parser)
    ast_generalizer = AstGeneralizer.find(language)()
    case.assertIsInstance(ast_generalizer, AstGeneralizer)
    unparser = Unparser.find(language)()
    case.assertIsInstance(unparser, Unparser)
    return parser, ast_generalizer, unparser


def _roundtrip_fortran(case, path, results_path, parser, ast_generalizer, unparser):
    with open(str(path)) as original_file:
        basic_check_fortran_code(case, path, original_file.read(), results=results_path,
                                 append_suffix=False)
    fortran_ast = parser.parse('', path)
    basic_check_fortran_ast(case, path, fortran_ast, results=results_path)
    tree = ast_generalizer.generalize(fortran_ast)
    basic_check_python_ast(case, path, tree, results=results_path)
    # python_code = python_unparser.unparse(tree)
    # basic_check_python_code(self, path, python_code, results=results_path)
    # tree = python_parser.parse(python_code)
    # basic_check_python_ast(self, path, tree, results=results_path)
    fortran_code = unparser.unparse(tree)
    basic_check_fortran_code(case, path, fortran_code, results=results_path)


def _migrate_fortran(case, path, results_path, parser, ast_generalizer, unparser):
    with open(str(path)) as original_file:
        basic_check_fortran_code(case, path, original_file.read(), results=results_path,
                                 append_suffix=False)
    fortran_ast = parser.parse('', path)
    basic_check_fortran_ast(case, path, fortran_ast, results=results_path)
    tree = ast_generalizer.generalize(fortran_ast)
    basic_check_python_ast(case, path, tree, results=results_path)
    python_code = unparser.unparse(tree)
    basic_check_python_code(case, path, python_code, results=results_path)


class Tests(unittest.TestCase):

    def _test_app(self, app_name, tools, test, dir_name=None):
        if app_name not in _APPS_ROOT_PATHS:
            return
        if dir_name is None:
            dir_name = app_name.lower()
        results_path = pathlib.Path(APPS_RESULTS_ROOT, dir_name)
        results_path.mkdir(exist_ok=True)
        self.assertGreater(len(_APPS_CODE_FILEPATHS[app_name]), 0, msg=_APPS_ROOT_PATHS[app_name])
        for path in _APPS_CODE_FILEPATHS[app_name]:
            with self.subTest(path=path):
                test(self, path, results_path, *tools)

    def test_roundrtip_miranda_io(self):
        self._test_app('miranda_io', _prepare_roundtrip(self, Language.find('Fortran')),
                       _roundtrip_fortran)

    def test_roundrtip_flash(self):
        self._test_app('FLASH', _prepare_roundtrip(self, Language.find('Fortran')),
                       _roundtrip_fortran)

    def test_roundrtip_ffbmini(self):
        """From https://github.com/fiber-miniapp/ffb-mini"""
        self._test_app('FFB-MINI', _prepare_roundtrip(self, Language.find('Fortran')),
                       _roundtrip_fortran)
