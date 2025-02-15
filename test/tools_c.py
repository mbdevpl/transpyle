"""Tools for testing C language support."""

import io
import unittest

import pycparser.c_ast

from .common import basic_check_ast


def c_ast_dump(node: pycparser.c_ast.Node) -> str:
    io_ = io.StringIO()
    node.show(io_, attrnames=True, nodenames=True, showcoord=True)
    return io_.getvalue()


def basic_check_c_ast(case: unittest.TestCase, path, c_tree, **kwargs):
    basic_check_ast(case, path, c_tree, pycparser.c_ast.FileAST, '.yaml', c_ast_dump, **kwargs)
