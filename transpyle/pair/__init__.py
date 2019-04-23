"""Python as IR (intermediate representation)."""

import typed_ast.ast3 as typed_ast3

from .ast_annotations import annotate_ast, has_annotation, has_annotations, get_annotation
from .assertions import function_returns, returns_array, is_ast_none, syntax_matches
from .ast_query import SyntaxFinder, ReturnFinder
from .manipulate import fix_stmts_in_body, separate_args_and_keywords, convert_return_to_assign
from .code_manipulation import replace_line, replace_scope
from .synthetic_ast import \
    make_range_call, make_call_from_slice, make_expression_from_slice, make_slice_from_call, \
    make_numpy_constructor, make_st_ndarray
from .inlining import CallInliner, inline_syntax, inline
from .loop_annotations import annotate_loop_syntax

__all__ = [
    'annotate_ast', 'has_annotation', 'has_annotations', 'get_annotation',
    'function_returns', 'returns_array', 'is_ast_none', 'syntax_matches',
    'SyntaxFinder', 'ReturnFinder',
    'fix_stmts_in_body', 'separate_args_and_keywords', 'convert_return_to_assign',
    'replace_line', 'replace_scope',
    'make_range_call', 'make_call_from_slice', 'make_expression_from_slice', 'make_slice_from_call',
    'make_numpy_constructor', 'make_st_ndarray',
    'CallInliner', 'inline_syntax', 'inline',
    'annotate_loop_syntax']


def _match_subscripted_attributed_name(tree, name: str, attr: str) -> bool:
    return isinstance(tree, typed_ast3.Subscript) \
        and isinstance(tree.value, typed_ast3.Attribute) \
        and isinstance(tree.value.value, typed_ast3.Name) \
        and tree.value.value.id == name and tree.value.attr == attr


def _match_array(tree) -> bool:
    return _match_subscripted_attributed_name(tree, 'st', 'ndarray')


def _match_io(tree) -> bool:
    return _match_subscripted_attributed_name(tree, 't', 'IO')
