"""Various assertions about AST."""

import logging
# import typing as t

import typed_ast.ast3 as typed_ast3

from .ast_query import syntax_name

_LOG = logging.getLogger(__name__)


def function_returns(function: typed_ast3.FunctionDef) -> bool:
    """Establish if a given function is not 'void'."""
    if is_ast_none(function.returns):
        return False
    if function.returns is None:
        # TODO: evaluate function body to find types of returned values (if any)
        return False
    return True


def returns_array(function) -> bool:
    returns = function.returns
    # returns.slice
    # returns.value.value
    # returns.value.attr
    return isinstance(returns, typed_ast3.Subscript) \
        and isinstance(returns.value, typed_ast3.Attribute) \
        and isinstance(returns.value.value, typed_ast3.Name) \
        and returns.value.value.id in ('np', 'st')


def is_ast_none(syntax) -> bool:
    return isinstance(syntax, typed_ast3.NameConstant) and syntax.value is None


def syntax_matches(syntax, target) -> bool:
    _01 = typed_ast3.dump(syntax)
    _02 = typed_ast3.dump(target)
    return _01 == _02
    # import ipdb; ipdb.set_trace()
    # raise TypeError()
    # return False


def names_equivalent(arg: str, value: typed_ast3.AST) -> bool:
    if isinstance(value, typed_ast3.Subscript):
        _LOG.warning('ignoring name subscripts when checking name equivalence')
        value = value.value
    try:
        name = syntax_name(value)
    except TypeError:
        _LOG.warning('cannot check name equivalence of %s', type(value))
        # import ipdb; ipdb.set_trace()
        return False
    return arg == name
