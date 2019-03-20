"""Examples for transpyle tests."""

import collections.abc
import datetime
import io
import itertools
import pathlib
import sys
import typing as t
import unittest
import xml.etree.ElementTree as ET

import pycparser.c_ast
import static_typing
import typed_ast.ast3
import typed_astunparse

_HERE = pathlib.Path(__file__).resolve().parent

RESULTS_ROOT = pathlib.Path(_HERE, 'results')
RESULTS_ROOT.mkdir(exist_ok=True)

EXAMPLES_LANGS = ('c11', 'cpp14', 'cython', 'f77', 'f95', 'python3')

EXAMPLES_LANGS_NAMES = {'c11': 'C11', 'cpp14': 'C++14', 'cython': 'Cython', 'f77': 'Fortran 77',
                        'f95': 'Fortran 95', 'python3': 'Python 3'}

EXAMPLES_EXTENSIONS = {
    'c11': ['.c', '.h'],
    'cpp14': ['.cpp', '.hpp'],
    'cython': ['.pyx'],
    'f77': ['.f'],
    'f95': ['.f90'],
    'python3': ['.py']}

EXAMPLES_ROOTS = {lang: pathlib.Path(_HERE, 'examples', lang) for lang in EXAMPLES_LANGS}

EXAMPLES_FILES = {lang: list(
    itertools.chain.from_iterable(EXAMPLES_ROOTS[lang].glob('**/*{}'.format(ext))
                                  for ext in EXAMPLES_EXTENSIONS[lang]))
                  for lang in EXAMPLES_LANGS}

EXAMPLES_RESULTS_ROOT = pathlib.Path(RESULTS_ROOT, 'examples')
EXAMPLES_RESULTS_ROOT.mkdir(exist_ok=True)
for _language_codename in EXAMPLES_LANGS:
    pathlib.Path(EXAMPLES_RESULTS_ROOT, _language_codename).mkdir(exist_ok=True)

APPS_RESULTS_ROOT = pathlib.Path(RESULTS_ROOT, 'apps')
APPS_RESULTS_ROOT.mkdir(exist_ok=True)


def basic_check_code(
        case: unittest.TestCase, path, code, language,
        results: pathlib.Path = EXAMPLES_RESULTS_ROOT, suffix: t.Union[bool, str] = True):
    """Check basic properties of given source code and dump it to file.

    suffix:
    if str, append it to filename
    """
    assert isinstance(code, str), type(code)
    if results == EXAMPLES_RESULTS_ROOT:
        results = results.joinpath(language)
        if not results.is_dir():
            results.mkdir()
    if suffix is True:
        suffix = EXAMPLES_EXTENSIONS[language][0]
    elif suffix is None or suffix is False:
        suffix = ''
    with results.joinpath(path.name + suffix).open('w') as result_file:
        result_file.write(code)


def basic_check_ast(
        case: unittest.TestCase, path, tree, tree_type: type, suffix: str, formatter=str,
        results: pathlib.Path = EXAMPLES_RESULTS_ROOT):
    """Check basic properties of given AST and dump it to file."""
    case.assertIsInstance(tree, tree_type)
    if results == EXAMPLES_RESULTS_ROOT:
        results = results.joinpath(path.parent.name)
        if not results.is_dir():
            results.mkdir()
    with results.joinpath(path.name + suffix).open('w') as result_file:
        result_file.write(formatter(tree))


EXAMPLES_C11_FILES = EXAMPLES_FILES['c11']


def c_ast_dump(node: pycparser.c_ast.Node) -> str:
    io_ = io.StringIO()
    node.show(io_, attrnames=True, nodenames=True, showcoord=True)
    return io_.getvalue()


def basic_check_c_ast(case: unittest.TestCase, path, c_tree, **kwargs):
    basic_check_ast(case, path, c_tree, pycparser.c_ast.FileAST, '.yaml', c_ast_dump, **kwargs)


EXAMPLES_CPP14_FILES = EXAMPLES_FILES['cpp14']


def basic_check_cpp_code(case: unittest.TestCase, path, code, **kwargs):
    basic_check_code(case, path, code, 'cpp14', **kwargs)


def basic_check_cpp_ast(case: unittest.TestCase, path, fortran_ast, **kwargs):
    basic_check_ast(case, path, fortran_ast, ET.Element, '.xml',
                    lambda _: ET.tostring(_).decode().rstrip(), **kwargs)


def make_swig_tmp_folder(input_path):
    swig_output_dir = pathlib.Path(EXAMPLES_RESULTS_ROOT, input_path.parent.name, 'swig')
    if not swig_output_dir.is_dir():
        swig_output_dir.mkdir()
    output_dir = pathlib.Path(
        EXAMPLES_RESULTS_ROOT, input_path.parent.name, 'swig',
        'swig_tmp_{}'.format(datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')))
    if not output_dir.is_dir():
        output_dir.mkdir()
    return output_dir


EXAMPLES_CYTHON_FILES = EXAMPLES_FILES['cython']

EXAMPLES_F77_FILES = EXAMPLES_FILES['f77']
EXAMPLES_F95_FILES = EXAMPLES_FILES['f95']


def basic_check_fortran_code(case: unittest.TestCase, path, code, **kwargs):
    basic_check_code(case, path, code, 'f77', **kwargs)


def basic_check_fortran_ast(case: unittest.TestCase, path, fortran_ast, **kwargs):
    basic_check_ast(case, path, fortran_ast, ET.Element, '.xml',
                    lambda _: ET.tostring(_).decode().rstrip(), **kwargs)


def make_f2py_tmp_folder(input_path):
    f2py_root_dir = pathlib.Path(EXAMPLES_RESULTS_ROOT, input_path.parent.name, 'f2py')
    if not f2py_root_dir.is_dir():
        f2py_root_dir.mkdir()
    output_dir = pathlib.Path(
        EXAMPLES_RESULTS_ROOT, input_path.parent.name, 'f2py',
        'f2py_tmp_{}'.format(datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')))
    if not output_dir.is_dir():
        output_dir.mkdir()
    return output_dir


EXAMPLES_PY3_FILES = EXAMPLES_FILES['python3']

EXAMPLES_PY3_ORDINARY = [
    """a = 1""",
    """b = 2""",
    """print('abc')"""]

EXAMPLES_PY3_TYPE_COMMENTS = [
    """a = 1  # type: int""",
    """b = 2  # type: t.Optional[int]"""]

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
    if sys.version_info[:2] >= (3, 6):
        validator = static_typing.ast_manipulation.AstValidator[typed_ast.ast3]()
        validator.visit(tree)


def execute_on_all_language_fundamentals(*languages: t.Sequence[str]):
    return execute_on_examples(itertools.chain.from_iterable(
        (_ for _ in EXAMPLES_FILES[language] if _.name.startswith('fundamentals'))
        for language in languages))


def execute_on_all_language_examples(*languages: t.Sequence[str]):
    return execute_on_examples(itertools.chain.from_iterable(
        EXAMPLES_FILES[language] for language in languages))


def execute_on_examples(example_paths: t.Iterable[pathlib.Path]):
    assert isinstance(example_paths, collections.abc.Iterable), type(example_paths)

    def test_implementation_wrapper(test_function):
        def wrapped_test_implementation(test_case: unittest.TestCase):
            for input_path in example_paths:
                with test_case.subTest(input_path=input_path):
                    test_function(test_case, input_path)
        return wrapped_test_implementation
    return test_implementation_wrapper
