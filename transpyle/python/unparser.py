"""Unparsing Python."""

import ast
import logging
import re

import astunparse
import horast
import typed_ast.ast3
import typed_astunparse

from ..general import Language, Unparser

_LOG = logging.getLogger(__name__)


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
