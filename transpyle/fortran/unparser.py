"""Fortran unparsing."""

import ast
import io
import logging

from astunparse.unparser import INFSTR
import horast
import typed_ast.ast3 as typed_ast3
import typed_astunparse
from typed_astunparse.unparser import interleave

from ..general import Language, Unparser
from .ast_generalizer import FORTRAN_PYTHON_TYPE_PAIRS, PYTHON_TYPE_ALIASES

_LOG = logging.getLogger(__name__)

PYTHON_FORTRAN_TYPE_PAIRS = {value: key for key, value in FORTRAN_PYTHON_TYPE_PAIRS.items()}

for name, aliases in PYTHON_TYPE_ALIASES.items():
    for alias in aliases:
        PYTHON_FORTRAN_TYPE_PAIRS[alias] = PYTHON_FORTRAN_TYPE_PAIRS[name]

PYTHON_FORTRAN_INTRINSICS = {
    'np.zeros': '0',
    'np.argmin': 'minloc',
    'np.argmax': 'maxloc'
    }


class Fortran77UnparserBackend(horast.unparser.Unparser):

    lang_name = 'Fortran 77'

    def __init__(self, *args, indent: int = 2, fixed_form: bool = True, **kwargs):
        self._indent_level = indent
        self._fixed_form = fixed_form
        super().__init__(*args, **kwargs)

    def fill(self, text=''):
        if self._fixed_form:
            pass
        super().fill(text)
        #self.f.write("\n"+"    "*self._indent + text)

    def write(self, text):
        if self._fixed_form:
            pass
        super().write(text)

    def enter(self):
        self._indent += 1

    def _unsupported_syntax(self, tree):
        unparsed = 'invalid'
        try:
            unparsed = '"""{}"""'.format(typed_astunparse.unparse(tree).strip())
        except AttributeError:
            pass
        self.fill('unsupported_syntax')
        #raise SyntaxError('unparsing {} like """{}""" ({} in Python) is unsupported for {}'.format(
        #    tree.__class__.__name__, typed_ast3.dump(tree), unparsed, self.lang_name))

    def dispatch_var_type(self, tree):
        code = horast.unparse(tree)
        stripped_code = code.strip()
        if stripped_code in PYTHON_FORTRAN_TYPE_PAIRS:
            type_name, precision = PYTHON_FORTRAN_TYPE_PAIRS[stripped_code]
            self.write(type_name)
            if precision is not None:
                self.write('*')
                self.write(precision)
        elif isinstance(tree, typed_ast3.Subscript):
            val = tree.value
            sli = tree.slice
            if isinstance(val, typed_ast3.Attribute) and isinstance(val.value, typed_ast3.Name) \
                    and val.value.id == 'st' and val.attr == 'ndarray':
                assert isinstance(sli, typed_ast3.Index), typed_astunparse.dump(tree)
                assert isinstance(sli.value, typed_ast3.Tuple)
                assert len(sli.value.elts) == 2
                elts = sli.value.elts
                self.write('dimension(')
                self.dispatch(elts[0])
                self.write('), ')
                self.dispatch_var_type(elts[1])
        else:
            raise NotImplementedError(f'not yet implemented: {typed_astunparse.dump(tree)}')
            #self._unsupported_syntax(tree)
            #self.dispatch(tree)

    def dispatch_for_iter(self, tree):
        if not isinstance(tree, typed_ast3.Call) \
                or not isinstance(tree.func, typed_ast3.Name) or tree.func.id != 'range':
            self._unsupported_syntax(tree)
        first = True
        for arg in tree.args:
            if first:
                first = False
            else:
                self.write(", ")
            self.dispatch(arg)

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
        if isinstance(t.annotation, typed_ast3.NameConstant):
            assert t.annotation.value == None
            assert isinstance(t.target, typed_ast3.Name)
            assert t.target.id == 'implicit'
            self.fill()
            self.write('implicit none')
            return
        self.fill()
        self.dispatch_var_type(t.annotation)
        self.write(' :: ')
        self.dispatch(t.target)
        if t.value:
            self.write(" = ")
            self.dispatch(t.value)

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
        raise NotImplementedError(f'not yet implemented: {typed_astunparse.dump(t)}')

    def _Exec(self, t):
        raise NotImplementedError(f'not yet implemented: {typed_astunparse.dump(t)}')

    def _Print(self, t):
        raise NotImplementedError('old Python AST is not supported')

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
        self.write('\n')
        if t.decorator_list:
            self._unsupported_syntax(t)
        self.fill('subroutine ' + t.name + ' (')
        self.dispatch(t.args)
        self.write(')')
        if t.returns:
            _LOG.warning('skipping return')
            #raise NotImplementedError('not yet implemented: {}'.format(typed_astunparse.dump(t)))
            #self.write(' result ')
            #self.dispatch(t.returns)
        self.enter()
        self.dispatch(t.body)
        self.leave()
        self.fill('end subroutine ' + t.name)

    def _AsyncFunctionDef(self, t):
        self._unsupported_syntax(t)

    def _For(self, t):
        if hasattr(t, 'type_comment') and t.type_comment or t.orelse:
            self._unsupported_syntax(t)

        self.fill('do ')
        self.dispatch(t.target)
        self.write(" = ")
        self.dispatch_for_iter(t.iter)
        self.enter()
        self.dispatch(t.body)
        self.leave()
        self.fill('end do')

    def _AsyncFor(self, t):
        self._unsupported_syntax(t)

    def _If(self, t):
        if t.orelse:
            raise NotImplementedError('not yet implemented: {}'.format(typed_astunparse.dump(t)))

        self.fill('if ')
        self.dispatch(t.test)
        self.write(' then')
        self.enter()
        self.dispatch(t.body)
        self.leave()
        self.fill('end if')

    def _While(self, t):
        raise NotImplementedError('not yet implemented: {}'.format(typed_astunparse.dump(t)))

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
        raise NotImplementedError(f'not yet implemented: {typed_astunparse.dump(t)}')

    def _JoinedStr(self, t):
        raise NotImplementedError(f'not yet implemented: {typed_astunparse.dump(t)}')

    def _Name(self, t):
        self.write(t.id)

    def _NameConstant(self, t):
        if t.value is None:
            _LOG.error('unparsing invalid Fortran from """%s"""', typed_astunparse.dump(t))
        self.write({
            None: '.none.',
            False: '.false.',
            True: '.true.'}[t.value])

    def _Repr(self, t):
        self._unsupported_syntax(t)

    def _Num(self, t):
        repr_n = repr(t.n)
        self.write(repr_n.replace("inf", INFSTR))

    def _List(self, t):
        self.write('/ ')
        interleave(lambda: self.write(", "), self.dispatch, t.elts)
        self.write(' /')

    def _ListComp(self, t):
        raise NotImplementedError(f'not yet implemented: {typed_astunparse.dump(t)}')

    def _GeneratorExp(self, t):
        self._unsupported_syntax(t)

    def _SetComp(self, t):
        self._unsupported_syntax(t)

    def _DictComp(self, t):
        self._unsupported_syntax(t)

    def _comprehension(self, t):
        raise NotImplementedError(f'not yet implemented: {typed_astunparse.dump(t)}')

    def _IfExp(self, t):
        raise NotImplementedError(f'not yet implemented: {typed_astunparse.dump(t)}')

    def _Set(self, t):
        self._unsupported_syntax(t)

    def _Dict(self, t):
        self._unsupported_syntax(t)

    def _Tuple(self, t):
        interleave(lambda: self.write(', '), self.dispatch, t.elts)

    unop = {"Invert":"~", "Not": ".not.", "UAdd":"+", "USub":"-"}
    def _UnaryOp(self, t):
        self.write("(")
        self.write(self.unop[t.op.__class__.__name__])
        self.write(" ")
        self.dispatch(t.operand)
        self.write(")")
        raise NotImplementedError(f'not yet implemented: {typed_astunparse.dump(t)}')

    binop = {
        'Add': '+', 'Sub': '-', 'Mult': '*', #'Div': '/', 'Mod': '%',
        #'LShift': '<<', 'RShift': '>>', 'BitOr': '|', 'BitXor': '^', 'BitAnd': '&',
        'FloorDiv': '/', 'Pow': '**'}
    def _BinOp(self, t):
        if t.op.__class__.__name__ not in self.binop:
            raise NotImplementedError(f'not yet implemented: {typed_astunparse.dump(t)}')
        self.write('(')
        self.dispatch(t.left)
        self.write(' ' + self.binop[t.op.__class__.__name__] + ' ')
        self.dispatch(t.right)
        self.write(')')

    cmpops = {
        'Eq': '==', 'NotEq': '<>', 'Lt': '<', 'LtE': '<=', 'Gt': '>', 'GtE': '>='}
        #'Is': '===', 'IsNot': 'is not'}
    def _Compare(self, t):
        if len(t.ops) > 1 or len(t.comparators) > 1 \
                or any([o.__class__.__name__ not in self.cmpops for o in t.ops]):
            raise NotImplementedError('not yet implemented: {}'.format(typed_astunparse.dump(t)))
        super()._Compare(t)

    boolops = {ast.And: '.and.', ast.Or: '.or.', typed_ast3.And: '.and.', typed_ast3.Or: '.or.'}
    def _BoolOp(self, t):
        self.write("(")
        s = " %s " % self.boolops[t.op.__class__]
        interleave(lambda: self.write(s), self.dispatch, t.values)
        self.write(")")

    def _Attribute(self,t):
        code = typed_astunparse.unparse(t).strip()
        if code == 't.IO':
            self.write('integer')
        elif code == 'Fortran.file_handles':
            pass
        else:
            self._unsupported_syntax(t)

    def _Call(self, t):
        func_code = horast.unparse(t.func).strip()
        if func_code.startswith('np.'):
            if func_code not in PYTHON_FORTRAN_INTRINSICS:
                raise NotImplementedError(f'not yet implemented: {typed_astunparse.dump(t)}')
            self.write(PYTHON_FORTRAN_INTRINSICS[func_code])
            return
        super()._Call(t)
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
        #if isinstance(t.slice, typed_ast3.Index):
        #elif isinstance(t.slice, typed_ast3.Slice):
        #    raise NotImplementedError(f'not yet implemented: {typed_astunparse.dump(t)}')
        #elif isinstance(t.slice, typed_ast3.ExtSlice):
        #    raise NotImplementedError(f'not yet implemented: {typed_astunparse.dump(t)}')
        #else:
        #    raise ValueError()
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
        if t.annotation:
            self._unsupported_syntax(t)
        self.write(t.arg)

    # others
    def _arguments(self, t):
        if t.vararg or t.kwonlyargs or t.kw_defaults or t.kwarg or t.defaults:
            raise NotImplementedError(f'not yet implemented: {typed_astunparse.dump(t)}')
        super()._arguments(t)

    def _keyword(self, t):
        if t.arg is None:
            raise NotImplementedError(f'not yet implemented: {typed_astunparse.dump(t)}')
        super()._keyword(t)

    def _Lambda(self, t):
        self._unsupported_syntax(t)

    def _alias(self, t):
        self._unsupported_syntax(t)

    def _withitem(self, t):
        self._unsupported_syntax(t)

    def _Await(self, t):
        self._unsupported_syntax(t)


class Fortran77Unparser(Unparser):

    def __init__(self):
        super().__init__(Language.find('Fortran 77'))

    def unparse(self, tree, indent: int = 2, fixed_form: bool = True) -> str:
        stream = io.StringIO()
        Fortran77UnparserBackend(tree, file=stream, indent=indent, fixed_form=fixed_form)
        return stream.getvalue()


class Fortran2008Unparser(Unparser):

    def __init__(self):
        super().__init__(Language.find('Fortran 2008'))

    def unparse(self, tree, indent: int = 4, fixed_form: bool = False) -> str:
        raise NotImplementedError('not yet implemented')
