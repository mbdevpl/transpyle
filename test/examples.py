"""Examples for transpyle tests."""

import pathlib
import unittest
import xml.etree.ElementTree as ET

import typed_ast.ast3
import typed_astunparse

_HERE = pathlib.Path(__file__).resolve().parent

RESULTS_ROOT = pathlib.Path(_HERE, 'results')
RESULTS_ROOT.mkdir(exist_ok=True)

EXAMPLES_LANGS = ('c11', 'cpp14', 'cython', 'f77', 'f95', 'python3')

EXAMPLES_EXTENSIONS = {
    'c11': ['.c', '.h'],
    'cpp14': ['.cpp', '.hpp'],
    'cython': ['.pyx'],
    'f77': ['.f'],
    'f95': ['.f90'],
    'python3': ['.py']}

EXAMPLES_ROOTS = {lang: pathlib.Path(_HERE, 'examples', lang) for lang in EXAMPLES_LANGS}

EXAMPLES_FILES = {lang: list(EXAMPLES_ROOTS[lang].glob('**/*.*')) for lang in EXAMPLES_LANGS}

EXAMPLES_RESULTS_ROOT = pathlib.Path(RESULTS_ROOT, 'examples')
EXAMPLES_RESULTS_ROOT.mkdir(exist_ok=True)

APPS_RESULTS_ROOT = pathlib.Path(RESULTS_ROOT, 'apps')
APPS_RESULTS_ROOT.mkdir(exist_ok=True)


def basic_check_code(
        case: unittest.TestCase, path, code, language,
        results: pathlib.Path = EXAMPLES_RESULTS_ROOT, append_suffix: bool = True):
    case.assertIsInstance(code, str)
    if results == EXAMPLES_RESULTS_ROOT:
        results = results.joinpath(language)
        if not results.is_dir():
            results.mkdir()
    filename = path.name + (EXAMPLES_EXTENSIONS[language][0] if append_suffix else '')
    with open(results.joinpath(filename), 'w') as result_file:
        result_file.write(code)


def basic_check_ast(
        case: unittest.TestCase, path, tree, tree_type: type, suffix: str, formatter=str,
        results: pathlib.Path = EXAMPLES_RESULTS_ROOT):
    case.assertIsInstance(tree, tree_type)
    if results == EXAMPLES_RESULTS_ROOT:
        results = results.joinpath(path.parent.name)
        if not results.is_dir():
            results.mkdir()
    with open(results.joinpath(path.name + suffix), 'w') as result_file:
        result_file.write(formatter(tree))



EXAMPLES_C11_FILES = EXAMPLES_FILES['c11']
EXAMPLES_CPP14_FILES = EXAMPLES_FILES['cpp14']
EXAMPLES_CYTHON_FILES = EXAMPLES_FILES['cython']

EXAMPLES_F77_FILES = EXAMPLES_FILES['f77']
EXAMPLES_F95_FILES = EXAMPLES_FILES['f95']


def basic_check_fortran_code(case: unittest.TestCase, path, code, **kwargs):
    basic_check_code(case, path, code, 'f77', **kwargs)


def basic_check_fortran_ast(case: unittest.TestCase, path, fortran_ast, **kwargs):
    basic_check_ast(case, path, fortran_ast, ET.Element, '.xml',
                    lambda _: ET.tostring(_).decode().rstrip(), **kwargs)


EXAMPLES_PY3_FILES = EXAMPLES_FILES['python3']

EXAMPLES_PY3_ORDINARY = [
    """a = 1""",
    """b = 2""",
    """print('abc')"""]

EXAMPLES_PY3_TYPE_COMMENTS = [
    """a = 1 # type: int""",
    """b = 2 # type: t.Optional[int]"""]

EXAMPLES_PY3_COMMENTS = [
    """print('abc')\n# printing abc"""]

EXAMPLES_PY3 = (
    EXAMPLES_PY3_ORDINARY, EXAMPLES_PY3_ORDINARY + EXAMPLES_PY3_TYPE_COMMENTS,
    EXAMPLES_PY3_TYPE_COMMENTS + EXAMPLES_PY3_TYPE_COMMENTS + EXAMPLES_PY3_COMMENTS)


def basic_check_python_code(case: unittest.TestCase, path, code, **kwargs):
    basic_check_code(case, path, code, 'python3', **kwargs)


def basic_check_python_ast(case: unittest.TestCase, path, tree, **kwargs):
    basic_check_ast(case, path, tree, typed_ast.ast3.AST, '-ast.py', typed_astunparse.dump,
                    **kwargs)
