
import io
import logging

from astunparse.unparser import INFSTR
import horast
import typed_ast.ast3 as typed_ast3
import typed_ast.ast3
from typed_astunparse.unparser import interleave

from ..general import Language, Unparser
import ast

_LOG = logging.getLogger(__name__)

class Fortran77Unparser(horast.unparser.Unparser):

    lang_name = 'Fortran 77'

    def _unsupported_syntax(self, tree):
        raise SyntaxError('unparsing {} like """{}""" is unsupported for {}'.format(
            tree.__class__.__name__, typed_ast.ast3.dump(tree), self.lang_name))

    def _Import(self, t):
        if len(t.names) > 1:
            self._unsupported_syntax(t)
        name = t.names[0]
        if name.name in ('numpy', 'typing'):
            return
        self.fill("use ")
        interleave(lambda: self.write(", "), self.dispatch, t.names)

    def _ImportFrom(self, t):
        self._unsupported_syntax(t)

    #def _Assign(self, t):
    #    self.fill()
    #    for target in t.targets:
    #        self.dispatch(target)
    #        self.write(" = ")
    #    self.dispatch(t.value)

    def _AugAssign(self, t):
        self.fill()
        self.dispatch(t.target)
        self.write(" "+self.binop[t.op.__class__.__name__]+"= ")
        self.dispatch(t.value)

    def _AnnAssign(self, t):
        raise NotImplementedError('not yet implemented')

    #def _Return(self, t):
    #    self.fill("return")
    #    if t.value:
    #        self.write(" ")
    #        self.dispatch(t.value)

    def _Pass(self, t):
        self.fill("continue")

    def _Break(self, t):
        self.fill("exit")

    def _Continue(self, t):
        self.fill("cycle")

    def _Delete(self, t):
        self.fill("del ")
        interleave(lambda: self.write(", "), self.dispatch, t.targets)

    def _Assert(self, t):
        raise NotImplementedError('not yet implemented')

    def _Exec(self, t):
        raise NotImplementedError('not yet implemented')

    def _Print(self, t):
        raise NotImplementedError('not yet implemented')

    def _Global(self, t):
        self._unsupported_syntax(t)

    def _Nonlocal(self, t):
        self._unsupported_syntax(t)

    def _Yield(self, t):
        self._unsupported_syntax(t)

    def _YieldFrom(self, t):
        self._unsupported_syntax(t)

    def _Raise(self, t):
        self._unsupported_syntax(t)

    def _Try(self, t):
        self._unsupported_syntax(t)

    def _TryExcept(self, t):
        raise NotImplementedError('old Python AST is not supported')

    def _TryFinally(self, t):
        raise NotImplementedError('old Python AST is not supported')

    def _ExceptHandler(self, t):
        self._unsupported_syntax(t)

    def _ClassDef(self, t):
        self._unsupported_syntax(t)

    def _FunctionDef(self, t):
        self._generic_FunctionDef(t)

    def _AsyncFunctionDef(self, t):
        self._unsupported_syntax(t)

    def _For(self, t):
        raise NotImplementedError('not yet implemented')

    def _AsyncFor(self, t):
        self._unsupported_syntax(t)

    def _If(self, t):
        raise NotImplementedError('not yet implemented')

    def _While(self, t):
        raise NotImplementedError('not yet implemented')

    def _With(self, t):
        self._unsupported_syntax(t)

    def _AsyncWith(self, t):
        self._unsupported_syntax(t)

    # expr
    def _Bytes(self, t):
        self.write(repr(t.s))

    def _Str(self, tree):
        self.write(repr(tree.s))

    def _FormattedValue(self, t):
        raise NotImplementedError('not yet implemented')

    def _JoinedStr(self, t):
        raise NotImplementedError('not yet implemented')

    def _Name(self, t):
        self.write(t.id)

    def _NameConstant(self, t):
        self.write(repr(t.value))
        raise NotImplementedError('not yet implemented')

    def _Repr(self, t):
        self._unsupported_syntax(t)

    def _Num(self, t):
        repr_n = repr(t.n)
        self.write(repr_n.replace("inf", INFSTR))

    def _List(self, t):
        raise NotImplementedError('not yet implemented')

    def _ListComp(self, t):
        raise NotImplementedError('not yet implemented')

    def _GeneratorExp(self, t):
        self._unsupported_syntax(t)

    def _SetComp(self, t):
        self._unsupported_syntax(t)

    def _DictComp(self, t):
        self._unsupported_syntax(t)

    def _comprehension(self, t):
        raise NotImplementedError('not yet implemented')

    def _IfExp(self, t):
        raise NotImplementedError('not yet implemented')

    def _Set(self, t):
        self._unsupported_syntax(t)

    def _Dict(self, t):
        self._unsupported_syntax(t)

    def _Tuple(self, t):
        raise NotImplementedError('not yet implemented')

    unop = {"Invert":"~", "Not": ".not.", "UAdd":"+", "USub":"-"}
    def _UnaryOp(self, t):
        self.write("(")
        self.write(self.unop[t.op.__class__.__name__])
        self.write(" ")
        self.dispatch(t.operand)
        self.write(")")
        raise NotImplementedError('not yet implemented')

    binop = { "Add":"+", "Sub":"-", "Mult":"*", "Div":"/", "Mod":"%",
                    "LShift":"<<", "RShift":">>", "BitOr":"|", "BitXor":"^", "BitAnd":"&",
                    "FloorDiv":"/", "Pow": "**"}
    def _BinOp(self, t):
        self.write("(")
        self.dispatch(t.left)
        self.write(" " + self.binop[t.op.__class__.__name__] + " ")
        self.dispatch(t.right)
        self.write(")")
        raise NotImplementedError('not yet implemented')

    cmpops = {"Eq":"==", "NotEq":"<>", "Lt":"<", "LtE":"<=", "Gt":">", "GtE":">=",
                        "Is":"===", "IsNot":"is not"}
    def _Compare(self, t):
        self.write("(")
        self.dispatch(t.left)
        for o, e in zip(t.ops, t.comparators):
            self.write(" " + self.cmpops[o.__class__.__name__] + " ")
            self.dispatch(e)
        self.write(")")
        raise NotImplementedError('not yet implemented')

    boolops = {ast.And: '.and.', ast.Or: '.or.', typed_ast3.And: '.and.', typed_ast3.Or: '.or.'}
    def _BoolOp(self, t):
        self.write("(")
        s = " %s " % self.boolops[t.op.__class__]
        interleave(lambda: self.write(s), self.dispatch, t.values)
        self.write(")")

    def _Attribute(self,t):
        self._unsupported_syntax(t)

    #def _Call(self, t):
    #    self.dispatch(t.func)
    #    self.write("(")
    #    comma = False
    #    for e in t.args:
    #        if comma: self.write(", ")
    #        else: comma = True
    #        self.dispatch(e)
    #    for e in t.keywords:
    #        if comma: self.write(", ")
    #        else: comma = True
    #        self.dispatch(e)
    #    if sys.version_info[:2] < (3, 5):
    #        if t.starargs:
    #            if comma: self.write(", ")
    #            else: comma = True
    #            self.write("*")
    #            self.dispatch(t.starargs)
    #        if t.kwargs:
    #            if comma: self.write(", ")
    #            else: comma = True
    #            self.write("**")
    #            self.dispatch(t.kwargs)
    #    self.write(")")

    def _Subscript(self, t):
        self.dispatch(t.value)
        self.write("(")
        self.dispatch(t.slice)
        self.write(")")

    def _Starred(self, t):
        self._unsupported_syntax(t)

    # slice
    def _Ellipsis(self, t):
        self._unsupported_syntax(t)

    def _Index(self, t):
        self.dispatch(t.value)

    def _Slice(self, t):
        if t.lower:
            self.dispatch(t.lower)
        self.write(":")
        if t.upper:
            self.dispatch(t.upper)
        if t.step:
            self.write(":")
            self.dispatch(t.step)

    def _ExtSlice(self, t):
        interleave(lambda: self.write(', '), self.dispatch, t.dims)

    # argument
    def _arg(self, t):
        self.write(t.arg)
        raise NotImplementedError('not yet implemented')
        if t.annotation:
            self._unsupported_syntax(t)

    # others
    def _arguments(self, t):
        raise NotImplementedError('not yet implemented')
        first = True
        # normal arguments
        defaults = [None] * (len(t.args) - len(t.defaults)) + t.defaults
        for a,d in zip(t.args, defaults):
            if first:first = False
            else: self.write(", ")
            self.dispatch(a)
            if d:
                self.write("=")
                self.dispatch(d)

        # varargs, or bare '*' if no varargs but keyword-only arguments present
        if t.vararg or getattr(t, "kwonlyargs", False):
            if first: first = False
            else: self.write(", ")
            self.write("*")
            if t.vararg:
                if hasattr(t.vararg, 'arg'):
                    self.write(t.vararg.arg)
                    if t.vararg.annotation:
                        self.write(": ")
                        self.dispatch(t.vararg.annotation)
                else:
                    self.write(t.vararg)
                    if getattr(t, 'varargannotation', None):
                        self.write(": ")
                        self.dispatch(t.varargannotation)

        # keyword-only arguments
        if getattr(t, "kwonlyargs", False):
            for a, d in zip(t.kwonlyargs, t.kw_defaults):
                if first:first = False
                else: self.write(", ")
                self.dispatch(a),
                if d:
                    self.write("=")
                    self.dispatch(d)

        # kwargs
        if t.kwarg:
            if first:first = False
            else: self.write(", ")
            if hasattr(t.kwarg, 'arg'):
                self.write("**"+t.kwarg.arg)
                if t.kwarg.annotation:
                    self.write(": ")
                    self.dispatch(t.kwarg.annotation)
            else:
                self.write("**"+t.kwarg)
                if getattr(t, 'kwargannotation', None):
                    self.write(": ")
                    self.dispatch(t.kwargannotation)

    def _keyword(self, t):
        raise NotImplementedError('not yet implemented')
        if t.arg is None:
            # starting from Python 3.5 this denotes a kwargs part of the invocation
            self.write("**")
        else:
            self.write(t.arg)
            self.write("=")
        self.dispatch(t.value)

    def _Lambda(self, t):
        self._unsupported_syntax(t)

    def _alias(self, t):
        self._unsupported_syntax(t)

    def _withitem(self, t):
        self._unsupported_syntax(t)

    def _Await(self, t):
        self._unsupported_syntax(t)

class FortranUnparser(Unparser):

    def __init__(self):
        super().__init__(Language.find('Fortran 2008'))

    def unparse(self, tree: typed_ast.ast3.AST) -> str:
        stream = io.StringIO()
        Fortran77Unparser(tree, file=stream)
        return stream.getvalue()
