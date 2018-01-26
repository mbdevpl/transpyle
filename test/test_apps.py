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

_FORTRAN_SUFFIXES = ('.f', '.F', '.f90', '.F90')

_APPS_PARENT_PATHS = {
    'miranda_io': pathlib.Path('fortran'),
    'FLASH-4.5': pathlib.Path('fortran'),
    'FLASH-SUBSET': pathlib.Path('fortran'),
    'FFB-MINI': pathlib.Path('fortran')}

_APPS_ROOT_PATHS = {
    'miranda_io': pathlib.Path('miranda_io'),
    'FLASH-4.5': pathlib.Path('flash-4.5'),
    'FLASH-SUBSET': pathlib.Path('flash-subset', 'FLASH4.4'),
    'FFB-MINI': pathlib.Path('ffb-mini')}

_APPS_OPTIONAL = {'FLASH-4.5', 'FLASH-SUBSET'}

_APPS_ROOT_PATHS = {
    app: (pathlib.Path('..', path) if _HERE.parent.joinpath('..', path).is_dir()
          else pathlib.Path('..', '..', _APPS_PARENT_PATHS[app], path))
    for app, path in _APPS_ROOT_PATHS.items()}

_APPS_ROOT_PATHS = {
    app: _HERE.parent.joinpath(path).resolve() for app, path in _APPS_ROOT_PATHS.items()
    if app not in _APPS_OPTIONAL or _HERE.parent.joinpath(path).is_dir()}

_FLASH_COMMON_PATHS = [
    'physics/Hydro/HydroMain/unsplit/hy_uhd_getFaceFlux.F90',
    'physics/Hydro/HydroMain/split/MHD_8Wave/hy_8wv_interpolate.F90',
    'physics/Hydro/HydroMain/split/MHD_8Wave/hy_8wv_fluxes.F90',
    'physics/Eos/EosMain/Gamma/eos_idealGamma.F90',
    'physics/Hydro/HydroMain/split/MHD_8Wave/hy_8wv_sweep.F90',
    'physics/Hydro/HydroMain/unsplit/hy_uhd_DataReconstructNormalDir_MH.F90',
    'physics/Hydro/HydroMain/unsplit/hy_uhd_upwindTransverseFlux.F90',
    # 'physics/Hydro/HydroMain/unsplit/hy_uhd_TVDslope.F90',  # interface
    'physics/Hydro/HydroMain/unsplit/hy_uhd_Roe.F90']

_APPS_CODE_FILEPATHS = {
    'miranda_io': [pathlib.Path(_APPS_ROOT_PATHS['miranda_io'], 'miranda_io.f90')],
    'FLASH-4.5': [
        pathlib.Path(_APPS_ROOT_PATHS['FLASH-4.5'], 'source', pathlib.Path(input_path))
        for input_path in [
            ] + _FLASH_COMMON_PATHS] if 'FLASH-4.5' in _APPS_ROOT_PATHS else [],
    'FLASH-SUBSET': [
        pathlib.Path(_APPS_ROOT_PATHS['FLASH-SUBSET'], 'source', pathlib.Path(input_path))
        for input_path in [
            'physics/Hydro/HydroMain/simpleUnsplit/HLL/hy_hllUnsplit.F90',
            'physics/Hydro/HydroMain/unsplit/hy_uhd_TVDslope.F90'  # also in 4.5, but fails
            ] + _FLASH_COMMON_PATHS] if 'FLASH-SUBSET' in _APPS_ROOT_PATHS else [],
    'FFB-MINI': [
        pathlib.Path(root, name)
        for root, _, files in os.walk(str(pathlib.Path(_APPS_ROOT_PATHS['FFB-MINI'], 'src')))
        for name in files if pathlib.Path(name).suffix in _FORTRAN_SUFFIXES and name not in {
            'ddcom4.F',  # SyntaxError - just not implemented yet
            'ffb_mini_main.F90',  # NotImplementedError
            'f_test.F90',  # NotImplementedError
            'mod_maprof.F90',  # NotImplementedError
            # OFP fails for the following files
            # issues need to be resolved upstream or files need to be modified
            'bcgs3x.F', 'bcgsxe.F', 'calax3.F', 'callap.F', 'dd_mpi.F', 'e2plst.F', 'extrfn.F',
            'gfutil.f', 'grad3x.F', 'les3x.F', 'lesrop.F', 'lesrpx.F', 'lessfx.F', 'lrfnms.F',
            'makemesh.F90', 'miniapp_util.F', 'mfname.F', 'neibr2.F', 'nodlex.F', 'pres3e.F',
            'rcmelm.F', 'rfname.F', 'srfexx.F', 'vel3d1.F', 'vel3d2.F'}]}


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
        if app_name not in _APPS_ROOT_PATHS and app_name in _APPS_OPTIONAL:
            self.skipTest('{} directory not found'.format(app_name))
        if dir_name is None:
            dir_name = app_name.lower()
        results_path = pathlib.Path(APPS_RESULTS_ROOT, dir_name)
        results_path.mkdir(exist_ok=True)
        self.assertGreater(len(_APPS_CODE_FILEPATHS[app_name]), 0, msg=_APPS_ROOT_PATHS[app_name])
        for path in _APPS_CODE_FILEPATHS[app_name]:
            with self.subTest(path=path):
                test(self, path, results_path, *tools)

    def test_roundtrip_miranda_io(self):
        self._test_app('miranda_io', _prepare_roundtrip(self, Language.find('Fortran')),
                       _roundtrip_fortran)

    def test_roundtrip_flash_45(self):
        self._test_app('FLASH-4.5', _prepare_roundtrip(self, Language.find('Fortran')),
                       _roundtrip_fortran)

    def test_roundtrip_flash(self):
        self._test_app('FLASH-SUBSET', _prepare_roundtrip(self, Language.find('Fortran')),
                       _roundtrip_fortran)

    def test_roundtrip_ffbmini(self):
        self._test_app('FFB-MINI', _prepare_roundtrip(self, Language.find('Fortran')),
                       _roundtrip_fortran)
