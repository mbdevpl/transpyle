"""Unparse into C++."""

import ast
import io
import logging
import typing as t

import horast
import nuitka
import typed_ast.ast3 as typed_ast3

from ..general import Language, Unparser

_LOG = logging.getLogger(__name__)


def transpile_test():
    command = ['nuitka', '--module', '{}.py']
    raise NotImplementedError()


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

    def enter(self):
        self.write(' {')
        self._indent += 1

    def leave(self):
        super().leave()
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

    def _ClassDef(self, t):
        raise NotImplementedError('not supported yet')

    def _FunctionDef(self, t):
        if t.decorator_list:
            self._unsupported_syntax(t, ' with decorators')
        self.write('\n')
        self.fill()
        if t.returns is None:
            self.write('void')
        else:
            self.dispatch_type(t.returns)
        self.write(' {}('.format(t.name))
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

        raise NotImplementedError('not supported yet')

    def _While(self, t):
        raise NotImplementedError('not supported yet')

    def _With(self, t):
        self._unsupported_syntax(t)

    def _AsyncWith(self, t):
        self._unsupported_syntax(t)

    def _Attribute(self, t):
        if isinstance(t.value, typed_ast3.Name):
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

        super()._Call(t)
        # raise NotImplementedError('not supported yet')

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
        backend(tree, file=stream)
        return stream.getvalue()
