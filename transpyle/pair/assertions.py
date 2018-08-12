
import typing as t

import typed_ast.ast3 as typed_ast3


def function_returns(function: typed_ast3.FunctionDef) -> bool:
    """Establish if a given function is not 'void'."""
    if is_ast_none(function.returns):
        return False
    if function.returns is None:
        # TODO: evaluate function body to find types of returned values (if any)
        return False
    return True


def is_ast_none(syntax) -> bool:
    return isinstance(syntax, typed_ast3.NameConstant) and syntax.value is None


def syntax_matches(syntax, target):
    _01 = typed_ast3.dump(syntax)
    _02 = typed_ast3.dump(target)
    return _01 == _02
    # import ipdb; ipdb.set_trace()
    # raise TypeError()
    # return False
