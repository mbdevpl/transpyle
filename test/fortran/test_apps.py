"""Integration tests based on various scientific applications written in Fortran."""

import logging
import os
import pathlib
import unittest

from transpyle.general import Language, CodeReader, Parser, AstGeneralizer, Unparser, CodeWriter

from ..common import \
    basic_check_fortran_code, basic_check_fortran_ast, \
    basic_check_python_code, basic_check_python_ast, \
    APPS_ROOT, execute_on_examples
from ..test_apps import _prepare_roundtrip, AppTests

_LOG = logging.getLogger(__name__)


def _roundtrip_fortran(case, path, results_path, parser, ast_generalizer, unparser):
    with path.open() as original_file:
        basic_check_fortran_code(case, path, original_file.read(), results=results_path,
                                 suffix=None)
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
    with path.open() as original_file:
        basic_check_fortran_code(case, path, original_file.read(), results=results_path,
                                 suffix=None)
    fortran_ast = parser.parse('', path)
    basic_check_fortran_ast(case, path, fortran_ast, results=results_path)
    tree = ast_generalizer.generalize(fortran_ast)
    basic_check_python_ast(case, path, tree, results=results_path)
    python_code = unparser.unparse(tree)
    basic_check_python_code(case, path, python_code, results=results_path)


@unittest.skipIf(
    Language.find('Fortran') is None, 'skipping due to missing Fortran language support')
class FFBMiniTests(AppTests):

    app_name = 'FFB-MINI'

    app_source_folder = APPS_ROOT.joinpath('ffb-mini', 'src')

    paths = [
        pathlib.Path(root, name) for root, _, files in os.walk(str(app_source_folder))
        for name in files if pathlib.Path(name).suffix in ('.f', '.F', '.f90', '.F90')
        and name not in {
            'ddcom4.F',  # SyntaxError - just not implemented yet
            'ffb_mini_main.F90',  # NotImplementedError
            'f_test.F90',  # NotImplementedError
            'mod_maprof.F90',  # NotImplementedError
            # OFP fails for the following files
            # issues need to be resolved upstream or files need to be modified
            'bcgs3x.F', 'bcgsxe.F', 'calax3.F', 'callap.F', 'dd_mpi.F', 'e2plst.F', 'extrfn.F',
            'gfutil.f', 'grad3x.F', 'les3x.F', 'lesrop.F', 'lesrpx.F', 'lessfx.F', 'lrfnms.F',
            'makemesh.F90', 'miniapp_util.F', 'mfname.F', 'neibr2.F', 'nodlex.F', 'pres3e.F',
            'rcmelm.F', 'rfname.F', 'srfexx.F', 'vel3d1.F', 'vel3d2.F'}]

    @unittest.skipUnless(os.environ.get('TEST_LONG'), 'skipping long test')
    def test_roundtrip(self):
        self._test_app(_prepare_roundtrip(self, Language.find('Fortran')), _roundtrip_fortran)


@unittest.skipIf(
    Language.find('Fortran') is None, 'skipping due to missing Fortran language support')
class Flash5Tests(unittest.TestCase):

    app_name = 'FLASH5'

    app_source_folder = APPS_ROOT.joinpath('flash5', 'source')

    paths = path_selection_tree(app_source_folder, {
        # pathlib.Path('physics', 'Eos', 'EosMain', 'Helmholtz_starkiller',
        #              'SpeciesBased'): 'actual_eos.F90',  # access specifiers (i.e public/private)
        pathlib.Path('physics', 'Hydro', 'HydroMain', 'unsplit'): [
            'hy_getFaceFlux.F90',
            # 'hy_getRiemannState.F90',  # need to preprocess 1 macro
            'hy_TVDslope.F90',
            'hy_upwindTransverseFlux.F90', pathlib.Path('MHD', 'hy_eigenVector.F90')],
        pathlib.Path('physics', 'sourceTerms', 'Burn'): {
            'BurnMain': {
                'nuclearBurn': [
                    'Burn.F90', 'bn_burner.F90', 'bn_azbar.F90', 'bn_screen4.F90', 'bn_sneutx.F90',
                    'bn_mcord.F90'],
                pathlib.Path('nuclearBurn', 'Aprox13'): [
                    'bn_mapNetworkToSpecies.F90', 'bn_networkTable.F90', 'bn_networkRates.F90',
                    'bn_networkScreen.F90', 'bn_network.F90', 'bn_networkSparseJakob.F90',
                    'bn_networkSparsePointers.F90', 'bn_networkDenseJakob.F90', 'bn_gift.F90']},
            'BurnIntegrate': ['bn_netIntegrate.F90', 'bn_baderMa28.F90', 'bn_rosenMa28.F90']},
        pathlib.Path('Simulation'): 'Simulation_init.F90'
        })
    paths.append(app_source_folder.parent.joinpath('lib', 'ma28', 'source', 'Ma28.F90'))

    @unittest.skipUnless(os.environ.get('TEST_LONG'), 'skipping long test')
    @execute_on_examples(paths)
    def test_roundtrip(self, input_path):
        reader = CodeReader()
        fortran_code = reader.read_file(input_path)
        results_path = pathlib.Path(APPS_RESULTS_ROOT, 'flash5')
        results_path.mkdir(exist_ok=True)
        basic_check_fortran_code(self, input_path, fortran_code, results=results_path, suffix=None)
        parser = Parser.find(Language.find('Fortran'))()
        fortran_ast = parser.parse(fortran_code, input_path)
        basic_check_fortran_ast(self, input_path, fortran_ast, results=results_path)
        ast_generalizer = AstGeneralizer.find(Language.find('Fortran'))()
        syntax = ast_generalizer.generalize(fortran_ast)
        basic_check_python_ast(self, input_path, syntax, results=results_path)
        unparser = Unparser.find(Language.find('Fortran'))()
        code = unparser.unparse(syntax)
        basic_check_fortran_code(self, input_path, code, results=results_path)

    def test_partial_inline_burn(self):
        _ = self.app_source_folder.joinpath(
            'physics', 'sourceTerms', 'Burn', 'BurnMain', 'nuclearBurn')
        inlined_path = _.joinpath('Aprox13', 'bn_mapNetworkToSpecies.F90')
        target_path = _.joinpath('Burn.F90')

        reader = CodeReader()
        inlined_code = reader.read_file(inlined_path)
        target_code = reader.read_file(target_path)

        parser = Parser.find(Language.find('Fortran'))()
        inlined_fortran_ast = parser.parse(inlined_code, inlined_path)
        # inlined_fortran_ast = inlined_fortran_ast.find('.//subroutine')
        target_fortran_ast = parser.parse(target_code, target_path)

        ast_generalizer = AstGeneralizer.find(Language.find('Fortran'))()
        inlined_syntax = ast_generalizer.generalize(inlined_fortran_ast)
        inlined_function = inlined_syntax.body[-1]
        # TODO: implement object finding to find function
        target_syntax = ast_generalizer.generalize(target_fortran_ast)
        target_function = target_syntax.body[-1]
        # TODO: implement object finding to find function

        # import horast
        # print(horast.unparse(inlined_function))
        # print(horast.unparse(target_function))
        # import ipdb; ipdb.set_trace()

        # import static_typing
        inlined_syntax = inline_syntax(
            target_function, inlined_function,
            # globals_={'NSPECIES': 13, 'st': static_typing, **globals()},
            verbose=True)
        annotation = horast_nodes.OpenAccPragma('parallel loop')
        annotate_loop_syntax(inlined_syntax, annotation)

        unparser = Unparser.find(Language.find('Fortran'))()
        transformed_code = unparser.unparse(inlined_syntax)

        results_path = pathlib.Path(APPS_RESULTS_ROOT, 'flash5-inlined')
        results_path.mkdir(exist_ok=True)
        CodeWriter().write_file(transformed_code, results_path.joinpath('Burn.inlined_some.F90'))


@unittest.skipIf(
    Language.find('Fortran') is None, 'skipping due to missing Fortran language support')
@unittest.skipUnless(os.environ.get('TEST_MIRANDA'), 'skipping tests on MIRANDA code')
class MirandaIOTests(AppTests):

    app_name = 'miranda_io'

    app_source_folder = APPS_ROOT.joinpath('miranda_io')

    paths = [app_source_folder.joinpath('miranda_io.f90')]

    def test_roundtrip_miranda_io(self):
        self._test_app(_prepare_roundtrip(self, Language.find('Fortran')), _roundtrip_fortran)
