"""Unparse into C++."""

import ast
import io
import itertools
import logging
import typing as t

import horast
import typed_ast.ast3 as typed_ast3

from ..general import Language, Unparser

_LOG = logging.getLogger(__name__)


def match_range_call(node) -> bool:
    return isinstance(node, typed_ast3.Call) and isinstance(node.func, typed_ast3.Name) \
        and node.func.id == 'range' and len(node.args) in {1, 2, 3}


def inferred_range_args(node: typed_ast3.Call) -> t.Tuple[
        typed_ast3.AST, typed_ast3.AST, typed_ast3.AST]:
    """Return a tuple (begin, end, step) for a given range() call.

    Return 3-tuple even if in the call some of the arguments are skipped.
    """
    assert match_range_call(node), type(node)
    if len(node.args) == 1:
        return typed_ast3.Num(n=0), node.args[0], typed_ast3.Num(n=1)
    if len(node.args) == 2:
        return node.args[0], node.args[1], typed_ast3.Num(n=1)
    return tuple(node.args)


def _match_subscripted_attributed_name(tree, name: str, attr: str) -> bool:
    return isinstance(tree, typed_ast3.Subscript) \
        and isinstance(tree.value, typed_ast3.Attribute) \
        and isinstance(tree.value.value, typed_ast3.Name) \
        and tree.value.value.id == name and tree.value.attr == attr


PY_TO_CPP_TYPES = {
    'np.int16': 'int16_t',
    'np.int32': 'int32_t',
    'np.int64': 'int64_t',
    'np.double': 'double',
    'st.ndarray': 'std::valarray'}


def for_header_to_tuple(target, target_type, iter_) -> t.Tuple[
        typed_ast3.Assign, typed_ast3.AST, typed_ast3.AST]:
    if match_range_call(iter_):
        begin, end, step = inferred_range_args(iter_)
        # raise NotImplementedError('TODO')
    else:
        raise NotImplementedError('only range() iterator in for loops is currently supported')

    if target_type is None:
        init = typed_ast3.Assign(targets=[target], value=begin, type_comment=None)
    else:
        init = typed_ast3.AnnAssign(target=target, annotation=target_type, value=begin, simple=True)
    condition = typed_ast3.Compare(left=target, ops=[typed_ast3.Lt()], comparators=[end])
    increment = typed_ast3.AugAssign(target=target, op=typed_ast3.Add(), value=step)
    return init, condition, increment

# def get_for_header(for_: typed_ast3.For):
#    pass


class Cpp14UnparserBackend(horast.unparser.Unparser):

    """Implementation of C++14 unparser."""

    def __init__(self, *args, **kwargs):
        self._includes = {}
        super().__init__(*args, **kwargs)

    def enter(self, *, write_brace: bool = True):
        if write_brace:
            self.write(' {')
        # assert self._indent > 0
        self._indent += 1

    def leave(self, *, write_brace: bool = True):
        super().leave()
        if write_brace:
            self.fill('}')

    def dispatch_type(self, type_hint):
        _LOG.debug('dispatching type hint %s', type_hint)
        if isinstance(type_hint, typed_ast3.Subscript):
            if isinstance(type_hint.value, typed_ast3.Attribute) \
                    and isinstance(type_hint.value.value, typed_ast3.Name):
                unparsed = horast.unparse(type_hint.value).strip()
                self.write(PY_TO_CPP_TYPES[unparsed])
                if unparsed == 'st.ndarray':
                    self.write('<')
                    sli = type_hint.slice
                    self.write('>')
                return
            self._unsupported_syntax(type_hint)
        if isinstance(type_hint, typed_ast3.Attribute):
            if isinstance(type_hint.value, typed_ast3.Name):
                unparsed = horast.unparse(type_hint).strip()
                self.write(PY_TO_CPP_TYPES[unparsed])
                return
            self._unsupported_syntax(type_hint)
        if isinstance(type_hint, typed_ast3.NameConstant):
            assert type_hint.value is None
            self.write('void')
            return
        self.dispatch(type_hint)

    def _Expr(self, tree):
        super()._Expr(tree)
        self.write(';')

    def _Import(self, t):
        self.fill('/* Python import')
        # raise NotImplementedError('not supported yet')
        super()._Import(t)
        self.fill('*/')
        # #include "boost/multi_array.hpp"

    def _ImportFrom(self, t):
        raise NotImplementedError('not supported yet')

    def _Assign(self, t):
        super()._Assign(t)
        self.write(';')

    def _AugAssign(self, t):
        super()._AugAssign(t)
        self.write(';')

    def _AnnAssign(self, t):
        self.fill()
        if not t.simple:
            self._unsupported_syntax(t, ' which is not simple')
        self.dispatch_type(t.annotation)
        self.write(' ')
        self.dispatch(t.target)
        if t.value:
            self.write(' = ')
            self.dispatch(t.value)
            self.write(';')

    def _Return(self, t):
        super()._Return(t)
        self.write(';')

    def _Pass(self, t):
        self.fill(';')

    def _ClassDef(self, t):
        self.write('\n')
        if t.decorator_list:
            self._unsupported_syntax(t, ' with decorators')
        self.fill('class {}'.format(t.name))
        if t.bases:
            _LOG.warning('C++: assuming base classes are inherited as public')
            self.write(': public ')
            comma = False
            for e in t.bases:
                if comma:
                    self.write(', public ')
                else:
                    comma = True
                self.dispatch(e)
            for e in t.keywords:
                if comma:
                    self.write(', public ')
                else:
                    comma = True
                self.dispatch(e)

        self.enter()
        for stmt in t.body:
            if isinstance(stmt, typed_ast3.FunctionDef):
                self._FunctionDef(stmt, in_class=t)
            else:
                self.dispatch(stmt)
        self.leave()
        self.write(';')

        # raise NotImplementedError('not supported yet')

    constructor_and_destructor_names = {'__init__', '__del__'}

    supported_special_method_names = set()

    unsupported_special_method_names = {
        '__repr__', '__str__', '__bytes__', '__format__',
        '__lt__', '__le__', '__eq__', '__ne__', '__gt__', '__ge__',
        '__hash__', '__bool__',
        '__getattr__', '__getattribute__', '__setattr__', '__delattr__', '__dir__',
        '__call__',
        '__len__', '__length_hint__', '__getitem__', '__missing__', '__setitem__', '__delitem__',
        '__iter__', '__next__',
        '__reversed__', '__contains__',
        '__add__', '__sub__', '__mul__', '__matmul__', '__truediv__', '__floordiv__', '__mod__',
        '__divmod__', '__pow__', '__lshift__', '__rshift__', '__and__', '__xor__', '__or__',
        '__radd__', '__rsub__', '__rmul__', '__rmatmul__', '__rtruediv__', '__rfloordiv__',
        '__rmod__', '__rdivmod__', '__rpow__', '__rlshift__', '__rrshift__', '__rand__', '__rxor__',
        '__ror__',
        '__iadd__', '__isub__', '__imul__', '__imatmul__', '__itruediv__', '__ifloordiv__',
        '__imod__', '__ipow__', '__ilshift__', '__irshift__', '__iand__', '__ixor__', '__ior__',
        '__neg__', '__pos__', '__abs__', '__invert__', '__complex__', '__int__', '__float__',
        '__index__',
        '__round__', '__trunc__', '__floor__', '__ceil__',
        '__enter__', '__exit__',
        '__aiter__', '__anext__',
        '__aenter__', '__aexit__'}

    special_method_names = (constructor_and_destructor_names | supported_special_method_names
                            | unsupported_special_method_names)

    def _FunctionDef(self, t, *, in_class: typed_ast3.ClassDef = None):
        if t.decorator_list:
            self._unsupported_syntax(t, ' with decorators')
        self.write('\n')
        if in_class:
            self.leave(write_brace=False)
            if t.name in self.special_method_names:
                access = 'public'
            elif t.name.startswith('__'):
                access = 'private'
            elif t.name.startswith('_'):
                access = 'protected'
            else:
                _LOG.warning('unparsing function "%s" as public', t.name)
                access = 'public'
            self.fill('{}:'.format(access))
            self.enter(write_brace=False)
        self.fill()
        if in_class and t.name in self.unsupported_special_method_names:
            raise NotImplementedError('not supported yet')
        if not in_class or t.name not in self.constructor_and_destructor_names:
            if t.returns is None:
                self.write('void ')
            else:
                self.dispatch_type(t.returns)
                self.write(' ')
        if in_class and t.name == '__init__':
            self.write('{}'.format(in_class.name))
        elif in_class and t.name == '__del__':
            self.write('~{}'.format(in_class.name))
        else:
            self.write('{}'.format(t.name))
        self.write('(')
        if in_class:
            # skip 1st arg
            _ = t.args
            args = typed_ast3.arguments(_.args[1:], _.vararg, _.kwonlyargs, _.kwarg, _.defaults,
                                        _.kw_defaults)
            self.dispatch(args)
        else:
            self.dispatch(t.args)
        self.write(')')
        self.enter()
        self.dispatch(t.body)
        self.leave()

    def _AsyncFunctionDef(self, t):
        self._unsupported_syntax(t)

    def _For(self, t):
        self.fill('for (')
        init, cond, increment = for_header_to_tuple(t.target, t.resolved_type_comment, t.iter)
        self.dispatch(init)
        self.write(', ')
        self.dispatch(cond)
        self.write(', ')
        self.dispatch(increment)
        # self.dispatch(t.iter)
        self.write(')')
        self.enter()
        self.dispatch(t.body)
        self.leave()
        if t.orelse:
            self._unsupported_syntax(t)

    def _AsyncFor(self, t):
        self._unsupported_syntax(t)

    def _If(self, t):
        self.fill('if (')
        self.dispatch(t.test)
        self.write(')')
        self.enter()
        self.dispatch(t.body)
        self.leave()
        # collapse nested ifs into equivalent elifs.
        while t.orelse and len(t.orelse) == 1 and isinstance(t.orelse[0], (ast.If, typed_ast3.If)):
            t = t.orelse[0]
            self.fill("else if (")
            self.dispatch(t.test)
            self.write(')')
            self.enter()
            self.dispatch(t.body)
            self.leave()
        # final else
        if t.orelse:
            self.fill("else")
            self.enter()
            self.dispatch(t.orelse)
            self.leave()

    def _While(self, t):
        raise NotImplementedError('not supported yet')

    def _With(self, t):
        self._unsupported_syntax(t)

    def _AsyncWith(self, t):
        self._unsupported_syntax(t)

    def _Str(self, tree):
        if hasattr(tree, 'kind') and tree.kind:
            self._unsupported_syntax(t, ' with prefix')

        text = tree.s
        text_repr = repr(text)

        for delimiter in ('"""', "'''", '"', "'"):
            if text_repr.startswith(delimiter) and text_repr.endswith(delimiter):
                stripped_delimiter = delimiter
                stripped_repr = text_repr[len(delimiter):-len(delimiter)]
                break

        delimiter = '"'
        if stripped_delimiter != delimiter \
                and delimiter not in stripped_delimiter and delimiter in stripped_repr:
            escaped_delimiter = ''.join(['\\{}'.format(_) for _ in delimiter])
            text = stripped_repr.replace(delimiter, escaped_delimiter)
        self.write(delimiter)
        self.write(text)
        self.write(delimiter)

    def _Attribute(self, t):
        if isinstance(t.value, typed_ast3.Name):
            if t.value.id == 'self':
                self.write('this')
                self.write('->')
                self.write(t.attr)
                return
            unparsed = {
                ('a', 'shape'): '???',
                ('b', 'shape'): '???',
                ('c', 'shape'): '???',
                ('np', 'single'): 'int32_t',
                ('np', 'double'): 'int64_t',
                ('np', 'zeros'): 'boost::multi_array',
                ('st', 'ndarray'): 'boost::multi_array'
                }[t.value.id, t.attr]
            self.write(unparsed)
            return
        self.dispatch(t.value)
        self.write('.')
        self.write(t.attr)

    def _Call(self, t):
        if t.keywords:
            self._unsupported_syntax(t, ' with keyword arguments')

        func_name = horast.unparse(t.func).strip()

        if func_name == 'print':
            self._includes['iostream'] = True
            self.write('std::cout << ')
            comma = False
            for arg in itertools.chain(t.args, t.keywords):
                if comma:
                    self.write(" << ")
                else:
                    comma = True
                self.dispatch(arg)
            return

        super()._Call(t)

    def _Subscript(self, t):
        if isinstance(t.value, typed_ast3.Name) and t.value.id == 'Pointer':
            if isinstance(t.slice, typed_ast3.Index) \
                    and isinstance(t.slice.value, typed_ast3.Name) and t.slice.value.id == 'str':
                self.write('char')
            else:
                self.dispatch(t.slice)
            self.write('*')
            return
        super()._Subscript(t)

    def _arg(self, t):
        if t.annotation is None:
            self._unsupported_syntax(t, ' without annotation')
        self.dispatch(t.annotation)
        self.write(' ')
        self.write(t.arg)

    def _Comment(self, node):
        if node.eol:
            self.write(' //')
        else:
            self.fill('//')
        self.write(node.value.s)

    def _unsupported_syntax(self, tree, comment: str = ''):
        raise SyntaxError('unparsing {}{} to C++ is not supported'.format(type(tree), comment))


class Cpp14HeaderUnparserBackend(Cpp14UnparserBackend):

    def _FunctionDef(self, t):
        self.fill()
        if t.returns is None:
            self.write('void')
        else:
            self.dispatch_type(t.returns)
        self.write(' {}('.format(t.name))
        self.dispatch(t.args)
        self.write(');')


class Cpp14Unparser(Unparser):

    def __init__(self, headers: bool = False):
        super().__init__(Language.find('C++14'))
        self.headers = headers

    def unparse(self, tree) -> str:
        stream = io.StringIO()
        backend = Cpp14HeaderUnparserBackend if self.headers else Cpp14UnparserBackend
        instance = backend(tree, file=stream)
        includes = '\n'.join('#include <{}>'.format(_) for _ in instance._includes)
        return '{}{}{}'.format(includes, '\n' if includes else '', stream.getvalue())
