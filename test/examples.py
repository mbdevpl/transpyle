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


def basic_check_code(case: unittest.TestCase, path, code, language, results=EXAMPLES_RESULTS_ROOT):
    case.assertIsInstance(code, str)
    with open(results.joinpath(path.name + EXAMPLES_EXTENSIONS[language][0]), 'w') as result_file:
        result_file.write(code)


EXAMPLES_C11_FILES = EXAMPLES_FILES['c11']
EXAMPLES_CPP14_FILES = EXAMPLES_FILES['cpp14']
EXAMPLES_CYTHON_FILES = EXAMPLES_FILES['cython']

EXAMPLES_F77_FILES = EXAMPLES_FILES['f77']
EXAMPLES_F95_FILES = EXAMPLES_FILES['f95']


def basic_check_fortran_code(case: unittest.TestCase, path, code, results=EXAMPLES_RESULTS_ROOT):
    basic_check_code(case, path, code, 'f77', results=EXAMPLES_RESULTS_ROOT)


def basic_check_fortran_ast(
        case: unittest.TestCase, path, fortran_ast, results=EXAMPLES_RESULTS_ROOT):
    case.assertIsInstance(fortran_ast, ET.Element)
    with open(results.joinpath(path.name + '.xml'), 'w') as result_file:
        result_file.write(ET.tostring(fortran_ast).decode().rstrip())


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


def basic_check_python_code(case: unittest.TestCase, path, code, results=EXAMPLES_RESULTS_ROOT):
    basic_check_code(case, path, code, 'python3', results=EXAMPLES_RESULTS_ROOT)


def basic_check_python_ast(case: unittest.TestCase, path, tree, results=EXAMPLES_RESULTS_ROOT):
    case.assertIsInstance(tree, typed_ast.ast3.AST)
    with open(results.joinpath(path.name + '-ast.py'), 'w') as result_file:
        result_file.write(typed_astunparse.dump(tree))
