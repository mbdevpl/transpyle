"""Examples for transpyle tests."""

import collections.abc
import datetime
import io
import itertools
import os
import pathlib
import platform
import sys
import typing as t
import unittest
import xml.etree.ElementTree as ET

import numpy as np
import pycparser.c_ast
import static_typing as st
import typed_ast.ast3
import typed_astunparse

_HERE = pathlib.Path(__file__).resolve().parent

_ROOT = _HERE.parent

APPS_ROOT = pathlib.Path(os.environ.get('TEST_APPS_ROOT', _ROOT.parent)).resolve()

RESULTS_ROOT = pathlib.Path(_HERE, 'results')
RESULTS_ROOT.mkdir(exist_ok=True)


def now_timestamp():
    return datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')


def random_data(shape=None, dtype=np.int):
    if shape is None:
        return dtype(np.random.rand() * 1000)
    return (np.random.rand(*shape) * 1000).astype(dtype)


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

EXAMPLES_ROOT = pathlib.Path(_HERE, 'examples')

EXAMPLES_ROOTS = {lang: EXAMPLES_ROOT.joinpath(lang) for lang in EXAMPLES_LANGS}

EXAMPLES_FILES = {lang: list(
    itertools.chain.from_iterable(EXAMPLES_ROOTS[lang].glob('**/*{}'.format(ext))
                                  for ext in EXAMPLES_EXTENSIONS[lang]))
                  for lang in EXAMPLES_LANGS}

# for _ in EXAMPLES_CATEGORIES:
#     EXAMPLES_FILES[_] = list(EXAMPLES_ROOTS[_].glob('**/*.*'))

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


def make_tmp_folder(sub_path: pathlib.Path, input_path: pathlib.Path) -> pathlib.Path:
    parent_dir = EXAMPLES_RESULTS_ROOT.joinpath(input_path.parent.name, sub_path)
    if not parent_dir.is_dir():
        parent_dir.mkdir(parents=True)
    output_dir = parent_dir.joinpath(
        '{}_tmp_{}'.format(str(sub_path).replace(os.path.sep, '_'), now_timestamp()))
    if not output_dir.is_dir():
        output_dir.mkdir()
    return output_dir


def c_ast_dump(node: pycparser.c_ast.Node) -> str:
    io_ = io.StringIO()
    node.show(io_, attrnames=True, nodenames=True, showcoord=True)
    return io_.getvalue()


def basic_check_c_ast(case: unittest.TestCase, path, c_tree, **kwargs):
    basic_check_ast(case, path, c_tree, pycparser.c_ast.FileAST, '.yaml', c_ast_dump, **kwargs)


def basic_check_cpp_code(case: unittest.TestCase, path, code, **kwargs):
    basic_check_code(case, path, code, 'cpp14', **kwargs)


def basic_check_cpp_ast(case: unittest.TestCase, path, fortran_ast, **kwargs):
    basic_check_ast(case, path, fortran_ast, ET.Element, '.xml',
                    lambda _: ET.tostring(_).decode().rstrip(), **kwargs)


def make_swig_tmp_folder(input_path):
    return make_tmp_folder(pathlib.Path('swig'), input_path)


def basic_check_fortran_code(case: unittest.TestCase, path, code, **kwargs):
    basic_check_code(case, path, code, 'f77', **kwargs)


def basic_check_fortran_ast(case: unittest.TestCase, path, fortran_ast, **kwargs):
    basic_check_ast(case, path, fortran_ast, ET.Element, '.xml',
                    lambda _: ET.tostring(_).decode().rstrip(), **kwargs)


def make_f2py_tmp_folder(input_path):
    return make_tmp_folder(pathlib.Path('f2py'), input_path)


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
        validator = st.ast_manipulation.AstValidator[typed_ast.ast3]()
        validator.visit(tree)


def execute_on_language_fundamentals(*languages: t.Sequence[str], **filters):
    return execute_on_examples(itertools.chain.from_iterable(
        (_ for _ in EXAMPLES_FILES[language] if _.name.startswith('fundamentals'))
        for language in languages), **filters)


def execute_on_language_examples(*languages: t.Sequence[str], **filters):
    return execute_on_examples(itertools.chain.from_iterable(
        EXAMPLES_FILES[language] for language in languages), **filters)


def execute_on_examples(example_paths: t.Iterable[pathlib.Path], **filters):
    assert isinstance(example_paths, collections.abc.Iterable), type(example_paths)
    for filter_ in filters:
        assert filter_ in {'predicate', 'suffix', 'predicate_not', 'suffix_not'}, filter_

    def test_implementation_wrapper(test_function):
        def wrapped_test_implementation(test_case: unittest.TestCase):
            for input_path in example_paths:
                if 'suffix' in filters and input_path.suffix != filters['suffix']:
                    continue
                if 'suffix_not' in filters and input_path.suffix == filters['suffix_not']:
                    continue
                if 'predicate' in filters and not filters['predicate'](input_path):
                    continue
                if 'predicate_not' in filters and filters['predicate_not'](input_path):
                    continue
                with test_case.subTest(input_path=input_path):
                    test_function(test_case, input_path)
        return wrapped_test_implementation
    return test_implementation_wrapper


def accelerated(path):
    return 'openacc' in path.name or 'openmp' in path.name


MACHINE = platform.node()

PERFORMANCE_RESULTS_ROOT = RESULTS_ROOT.joinpath('performance', MACHINE, now_timestamp())

if not PERFORMANCE_RESULTS_ROOT.parent.parent.is_dir():
    PERFORMANCE_RESULTS_ROOT.parent.parent.mkdir()
if not PERFORMANCE_RESULTS_ROOT.parent.is_dir():
    PERFORMANCE_RESULTS_ROOT.parent.mkdir()
if not PERFORMANCE_RESULTS_ROOT.is_dir():
    PERFORMANCE_RESULTS_ROOT.mkdir()
