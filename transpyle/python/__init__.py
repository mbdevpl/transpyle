"""Python support for transpyle package."""

import inspect
import typing as t

import typed_ast.ast3 as typed_ast3

from ..general import \
    Language, Parser, AstGeneralizer, IdentityAstGeneralizer, Unparser, Translator, AutoTranspiler
from .parser import TypedPythonParserWithComments
from .unparser import TypedPythonUnparserWithComments
from .translator import PythonTranslator


Language.register(Language(['Python 3.5'], ['.py']), ['Python 3.5'])
Language.register(Language(['Python 3.6'], ['.py']), ['Python 3.6', 'Python 3', 'Python'])

Parser.register(TypedPythonParserWithComments,
                (Language.find('Python 3.5'), Language.find('Python 3.6')))


class PythonAstGeneralizer(IdentityAstGeneralizer):

    """Python doesn't need AST generalizer."""

    pass


AstGeneralizer.register(PythonAstGeneralizer,
                        (Language.find('Python 3.5'), Language.find('Python 3.6')))

Unparser.register(TypedPythonUnparserWithComments,
                  (Language.find('Python 3.5'), Language.find('Python 3.6')))

Translator.register(PythonTranslator, (Language.find('Python 3.5'), Language.find('Python 3.6')))


def make_range_call(begin: t.Optional[typed_ast3.AST] = None, end: typed_ast3.AST = None,
                    step: t.Optional[typed_ast3.AST] = None) -> typed_ast3.Call:
    """Create a typed_ast node equivalent to: range(begin, end, step)."""
    assert isinstance(end, typed_ast3.AST)
    if step is None:
        if begin is None:
            args = [end]
        else:
            args = [begin, end]
    else:
        assert isinstance(step, typed_ast3.AST)
        assert isinstance(begin, typed_ast3.AST)
        args = [begin, end, step]
    return typed_ast3.Call(func=typed_ast3.Name(id='range', ctx=typed_ast3.Load()),
                           args=args, keywords=[])


def make_numpy_constructor(function: str, arg: typed_ast3.AST,
                           data_type: typed_ast3.AST) -> typed_ast3.Call:
    return typed_ast3.Call(
        func=typed_ast3.Attribute(
            value=typed_ast3.Name(id='np'), attr=function, ctx=typed_ast3.Load()),
        args=[arg],
        keywords=[typed_ast3.keyword(arg='dtype', value=data_type)])


def make_st_ndarray(data_type: typed_ast3.AST,
                    dimensions_or_sizes: t.Union[int, list]) -> typed_ast3.Subscript:
    """Create a typed_ast node equivalent to: st.ndarray[dimensions, data_type, sizes]."""
    if isinstance(dimensions_or_sizes, int):
        dimensions = dimensions_or_sizes
        sizes = None
    else:
        dimensions = len(dimensions_or_sizes)
        sizes = [_ for _ in dimensions_or_sizes]
    return typed_ast3.Subscript(
        value=typed_ast3.Attribute(
            value=typed_ast3.Name(id='st', ctx=typed_ast3.Load()),
            attr='ndarray', ctx=typed_ast3.Load()),
        slice=typed_ast3.Index(value=typed_ast3.Tuple(
            elts=[typed_ast3.Num(n=dimensions), data_type] +
            [typed_ast3.Tuple(elts=sizes)] if sizes else [])),
        ctx=typed_ast3.Load())


STANDALONE_EXPRESSION_TYPES = (
    typed_ast3.Call, typed_ast3.UnaryOp, typed_ast3.BinOp, typed_ast3.BoolOp,
    typed_ast3.Compare, typed_ast3.IfExp, typed_ast3.Attribute, typed_ast3.Name,
    typed_ast3.Subscript, typed_ast3.Num, typed_ast3.Str, typed_ast3.FormattedValue,
    typed_ast3.JoinedStr, typed_ast3.Bytes, typed_ast3.List, typed_ast3.Tuple,
    typed_ast3.Set, typed_ast3.Dict, typed_ast3.Ellipsis, typed_ast3.NameConstant)


def fix_stmts_in_body(stmts: t.List[typed_ast3.AST]) -> t.List[typed_ast3.AST]:
    assert isinstance(stmts, list)
    return [typed_ast3.Expr(value=stmt) if isinstance(stmt, STANDALONE_EXPRESSION_TYPES)
            else stmt for stmt in stmts]


def transpile(function_or_class, to_language: Language, *args, **kwargs):
    """Instantiate Python transpiler to transpile one function or class.

    Meant to be used as decorator."""
    transpiler = AutoTranspiler(Language.find('Python 3'), to_language)
    return transpiler.transpile(function_or_class)
