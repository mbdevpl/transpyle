"""Python as IR (intermediate representation)."""

import typing as t

import typed_ast.ast3 as typed_ast3

from .assertions import function_returns, syntax_matches
from .manipulate import fix_stmts_in_body, separate_args_and_keywords
from .synthetic_ast import make_range_call, make_numpy_constructor, make_st_ndarray


def _match_subscripted_attributed_name(tree, name: str, attr: str) -> bool:
    return isinstance(tree, typed_ast3.Subscript) \
        and isinstance(tree.value, typed_ast3.Attribute) \
        and isinstance(tree.value.value, typed_ast3.Name) \
        and tree.value.value.id == name and tree.value.attr == attr


def _match_array(tree) -> bool:
    return _match_subscripted_attributed_name(tree, 'st', 'ndarray')


def _match_io(tree) -> bool:
    return _match_subscripted_attributed_name(tree, 't', 'IO')


def returns_array(function):
    returns = function.returns
    # returns.slice
    # returns.value.value
    # returns.value.attr
    return isinstance(returns, typed_ast3.Subscript) \
        and isinstance(returns.value, typed_ast3.Attribute) \
        and isinstance(returns.value.value, typed_ast3.Name) \
        and returns.value.value.id in ('np', 'st')
