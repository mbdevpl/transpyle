
import typing as t

import typed_ast.ast3 as typed_ast3


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
        # assert all(isinstance(_, typed_ast3.Index) for _ in dimensions_or_sizes), dimensions_or_sizes
        # sizes = [_ for _ in dimensions_or_sizes]
        sizes = []
        for size in dimensions_or_sizes:
            if isinstance(size, typed_ast3.Index):
                size = size.value
            elif isinstance(size, typed_ast3.Slice):
                lower, upper, step = size.lower, size.upper, size.step
                if lower is None and upper is None and step is None:
                    size = typed_ast3.Call(typed_ast3.Name('slice', typed_ast3.Load()), [], [])
                elif lower is None and upper is not None and step is None:
                    size = upper
                elif lower is not None and upper is not None and step is None:
                    size = typed_ast3.Call(typed_ast3.Name('slice', typed_ast3.Load()),
                                           [lower, upper], [])
                elif lower is not None and upper is None and step is None:
                    size = typed_ast3.Call(typed_ast3.Name('slice', typed_ast3.Load()),
                                           [lower, typed_ast3.NameConstant(None)], [])
                else:
                    raise NotImplementedError('unsupported size form: "{}"'
                                              .format(typed_ast3.dump(size)))
                # assert size.lower is None \
                #    or isinstance(size.lower, typed_ast3.Num) and size.lower.n == 0, size.lower
                # assert size.step is None \
                #    or isinstance(size.step, typed_ast3.Num) and size.step.n == 1, size.step
                # assert size.upper is not None, typed_ast3.dump(size)
            # elif isinstance(size, typed_ast3.ExtSlice):
            #    size = size.dims
            else:
                raise NotImplementedError('unsupported size type: "{}"'.format(type(size)))
            sizes.append(size)
    return typed_ast3.Subscript(
        value=typed_ast3.Attribute(
            value=typed_ast3.Name(id='st', ctx=typed_ast3.Load()),
            attr='ndarray', ctx=typed_ast3.Load()),
        slice=typed_ast3.Index(value=typed_ast3.Tuple(
            elts=[typed_ast3.Num(n=dimensions), data_type] + [
                typed_ast3.Tuple(elts=sizes, ctx=typed_ast3.Load())] if sizes else [],
            ctx=typed_ast3.Load())),
        ctx=typed_ast3.Load())
