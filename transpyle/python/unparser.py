"""Unparsers for Python."""

import ast
import logging
import re

import astunparse
import horast
import typed_ast.ast3
import typed_astunparse

from ..general import Language, Unparser
from .parser import COMMENT_FULL_PREFIX, COMMENT_SUFFIX, DIRECTIVE_FULL_PREFIX, DIRECTIVE_SUFFIX


_LOG = logging.getLogger(__name__)

_DELIM = '''(['"]|\'\'\'|""")'''
_COMMENT_PATTERN = re.compile(
    r"\s*" + _DELIM + COMMENT_FULL_PREFIX + ".*" + COMMENT_SUFFIX + _DELIM)
_DIRECTIVE_PATTERN = re.compile(r"\s*" + _DELIM + DIRECTIVE_FULL_PREFIX + ".*" + DIRECTIVE_SUFFIX + _DELIM)

_RAW_COMMENT_PREFIX_PATTERN = re.compile(_DELIM + COMMENT_FULL_PREFIX)
_RAW_COMMENT_SUFFIX_PATTERN = re.compile(COMMENT_SUFFIX + _DELIM)
_RAW_DIRECTIVE_PREFIX_PATTERN = re.compile(_DELIM + DIRECTIVE_FULL_PREFIX)
_RAW_DIRECTIVE_SUFFIX_PATTERN = re.compile(DIRECTIVE_SUFFIX + _DELIM)


def postprocess_python_code(code: str) -> str:

    changed = False

    lines = code.splitlines()
    for i, line in enumerate(lines):
        if _COMMENT_PATTERN.fullmatch(line):
            line = _RAW_COMMENT_PREFIX_PATTERN.sub('#', line, 1)
            line = _RAW_COMMENT_SUFFIX_PATTERN.sub('', line, 1)
            lines[i] = line
        elif _DIRECTIVE_PATTERN.fullmatch(line):
            line = _RAW_DIRECTIVE_PREFIX_PATTERN.sub('# pragma: ', line, 1)
            line = _RAW_DIRECTIVE_SUFFIX_PATTERN.sub('', line, 1)
            lines[i] = line
        else:
            continue
        changed = True

    if changed:
        code = '\n'.join(lines) + '\n'

    if len(code) > 1 and code[0] == '\n':
        return code[1:]
    return code


class NativePythonUnparser(Unparser):

    """Generate Python 3 source code from native AST using astunparse package."""

    def __init__(self):
        super().__init__(Language.find('Python 3'))

    def unparse(self, tree: ast.AST) -> str:
        code = astunparse.unparse(tree)
        return code

    def dump(self, tree) -> str:
        return astunparse.dump(tree)


class TypedPythonUnparser(NativePythonUnparser):

    def unparse(self, tree: typed_ast.ast3.AST) -> str:
        code = typed_astunparse.unparse(tree)
        return code

    def dump(self, tree) -> str:
        return typed_astunparse.dump(tree)


class TypedPythonUnparserWithComments(TypedPythonUnparser):

    def unparse(self, tree: typed_ast.ast3.AST) -> str:
        code = horast.unparse(tree)
        return code
