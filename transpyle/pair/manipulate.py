
import typing as t

import typed_ast.ast3 as typed_ast3


STANDALONE_EXPRESSION_TYPES = (
    typed_ast3.Call, typed_ast3.UnaryOp, typed_ast3.BinOp, typed_ast3.BoolOp,
    typed_ast3.Compare, typed_ast3.IfExp, typed_ast3.Attribute, typed_ast3.Name,
    typed_ast3.Subscript, typed_ast3.Num, typed_ast3.Str, typed_ast3.FormattedValue,
    typed_ast3.JoinedStr, typed_ast3.Bytes, typed_ast3.List, typed_ast3.Tuple,
    typed_ast3.Set, typed_ast3.Dict, typed_ast3.Ellipsis, typed_ast3.NameConstant)


def fix_stmts_in_body(stmts: t.List[typed_ast3.AST]) -> t.List[typed_ast3.AST]:
    assert isinstance(stmts, list)
    if not stmts:
        return [typed_ast3.Pass()]
    return [typed_ast3.Expr(value=stmt) if isinstance(stmt, STANDALONE_EXPRESSION_TYPES)
            else stmt for stmt in stmts]


def separate_args_and_keywords(args_and_keywords):
    args = []
    keywords = []
    for arg in args_and_keywords:
        if isinstance(arg, typed_ast3.keyword):
            keywords.append(arg)
        else:
            args.append(arg)
    assert all(not isinstance(_, typed_ast3.keyword) for _ in args), args
    return args, keywords
