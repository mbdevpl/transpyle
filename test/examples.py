"""Examples for transpyle tests."""

import pathlib

_HERE = pathlib.Path(__file__).resolve().parent

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

EXAMPLES_C11_FILES = EXAMPLES_FILES['c11']
EXAMPLES_CPP14_FILES = EXAMPLES_FILES['cpp14']
EXAMPLES_CYTHON_FILES = EXAMPLES_FILES['cython']
EXAMPLES_F77_FILES = EXAMPLES_FILES['f77']
EXAMPLES_F95_FILES = EXAMPLES_FILES['f95']
EXAMPLES_PY3_FILES = EXAMPLES_FILES['python3']
