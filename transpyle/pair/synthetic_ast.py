"""Functions for creating a synthetic AST."""

import typing as t

import typed_ast.ast3 as typed_ast3

from .assertions import is_ast_none


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


def make_call_from_slice(slice_: typed_ast3.Slice) -> typed_ast3.Call:
    """Transform code like '0:n:2' into 'slice(0, n, 2)'."""
    assert isinstance(slice_, typed_ast3.Slice), type(slice_)
    lower, upper, step = slice_.lower, slice_.upper, slice_.step
    if lower is None and upper is None and step is None:
        args = []
    elif lower is not None and upper is None and step is None:
        args = [lower, typed_ast3.NameConstant(None)]
    elif lower is None and upper is not None and step is None:
        args = [typed_ast3.NameConstant(None), upper]
    elif lower is not None and upper is not None and step is None:
        args = [lower, upper]
    elif lower is not None and upper is None and step is not None:
        args = [lower, typed_ast3.NameConstant(None), step]
    elif lower is not None and upper is not None and step is not None:
        args = [lower, upper, step]
    else:
        raise NotImplementedError('unsupported slice form: "{}"'.format(typed_ast3.dump(slice_)))
    return typed_ast3.Call(typed_ast3.Name('slice', typed_ast3.Load()), args, [])


def make_expression_from_slice(
        slice_: t.Union[typed_ast3.Index, typed_ast3.Slice, typed_ast3.ExtSlice]) -> typed_ast3.AST:
    """Transform code like '0:n:2' into a valid expression that is as simple as possible."""
    assert isinstance(slice_, (
        typed_ast3.Index, typed_ast3.Slice, typed_ast3.ExtSlice)), type(slice_)

    if isinstance(slice_, typed_ast3.Index):
        return slice_.value
    if isinstance(slice_, typed_ast3.Slice):
        lower, upper, step = slice_.lower, slice_.upper, slice_.step
        if lower is None and upper is not None and step is None:
            return upper
        return make_call_from_slice(slice_)
    assert isinstance(slice_, typed_ast3.ExtSlice)
    elts = [make_expression_from_slice(dim) for dim in slice_.dims]
    return typed_ast3.Tuple(elts=elts, ctx=typed_ast3.Load())


def make_slice_from_call(call: typed_ast3.Call) -> typed_ast3.Slice:
    """Transform code like 'slice(0, n, 2)' into '0:n:2'."""
    assert isinstance(call, typed_ast3.Call), type(call)
    assert isinstance(call.func, typed_ast3.Name), type(call.func)
    assert call.func.id == 'slice', call.func.id
    assert len(call.args) in {0, 1, 2, 3}, len(call.args)
    if not call.args:
        return typed_ast3.Slice(lower=None, upper=None, step=None)
    if len(call.args) == 1:
        return typed_ast3.Slice(lower=None, upper=call.args[0], step=None)
    lower = call.args[0]
    upper = call.args[1]
    step = call.args[2] if len(call.args) == 3 else None
    lower, upper, step = [(None if is_ast_none(_) else _) for _ in (lower, upper, step)]
    return typed_ast3.Slice(lower=lower, upper=upper, step=step)


def make_numpy_constructor(function: str, arg: typed_ast3.AST,
                           data_type: typed_ast3.AST) -> typed_ast3.Call:
    return typed_ast3.Call(
        func=typed_ast3.Attribute(
            value=typed_ast3.Name(id='np', ctx=typed_ast3.Load()),
            attr=function, ctx=typed_ast3.Load()),
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
        sizes = [make_expression_from_slice(size) for size in dimensions_or_sizes]
    return typed_ast3.Subscript(
        value=typed_ast3.Attribute(
            value=typed_ast3.Name(id='st', ctx=typed_ast3.Load()),
            attr='ndarray', ctx=typed_ast3.Load()),
        slice=typed_ast3.Index(value=typed_ast3.Tuple(
            elts=[typed_ast3.Num(n=dimensions), data_type] + [
                typed_ast3.Tuple(elts=sizes, ctx=typed_ast3.Load())] if sizes else [],
            ctx=typed_ast3.Load())),
        ctx=typed_ast3.Load())
