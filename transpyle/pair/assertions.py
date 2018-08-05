
import typing as t

import typed_ast.ast3 as typed_ast3


def function_returns(function: typed_ast3.FunctionDef):
    return function.returns is not None \
        and not isinstance(function.returns, typed_ast3.NameConstant)
    # TODO: validate further


def syntax_matches(syntax, target):
    raise TypeError()
    return False
