"""C AST generalization."""

import logging
import typing as t

import pycparser.c_ast as c_ast
import typed_ast.ast3 as typed_ast3

from ..pair import make_range_call, fix_stmts_in_body
from ..general import Language, AstGeneralizer

_LOG = logging.getLogger(__name__)


def _node_debug(node: c_ast.Node):
    if isinstance(node, c_ast.Node):
        return _node_str(node)
    if isinstance(node, tuple):
        return tuple([_node_debug(_) for _ in node])
    if isinstance(node, list):
        return [_node_debug(_) for _ in node]
    raise NotImplementedError()


def _node_str(node: c_ast.Node):
    return '{}({})'.format(type(node), {_: getattr(node, _) for _ in node.__slots__})


C_UNARY_OPERATORS_TO_PYTHON = {
    'sizeof': (typed_ast3.Call, 'sizeof'),
    '++': (typed_ast3.AugAssign, typed_ast3.Add)}

C_BINARY_OPERATORS_TO_PYTHON = {
    '==': (typed_ast3.Compare, typed_ast3.Eq),
    '!=': (typed_ast3.Compare, typed_ast3.NotEq),
    '<': (typed_ast3.Compare, typed_ast3.Lt),
    '>': (typed_ast3.Compare, typed_ast3.Gt),
    '+': (typed_ast3.BinOp, typed_ast3.Add),
    '*': (typed_ast3.BinOp, typed_ast3.Mult)}

C_ASSIGNMENT_OPERATORS_TO_PYTHON = {
    '=': (typed_ast3.Assign, None),
    '+=': (typed_ast3.AugAssign, typed_ast3.Add)}

INITIALIZABLE_DECLARATIONS = (c_ast.ArrayDecl, c_ast.PtrDecl, c_ast.TypeDecl)

DECL_DATA_LENGTHS = {c_ast.FuncDecl: 3, c_ast.ArrayDecl: 2, c_ast.PtrDecl: 2, c_ast.TypeDecl: 2}


class CAstGeneralizerBackend(c_ast.NodeVisitor):  # pylint: disable=too-many-public-methods

    """Traverse pycparser's nodes and convert them to typed_ast.ast3 nodes.

    Use pycparser's NodeVisitor class.
    """

    # def __init__(self):
    #    super().__init__()

    def visit(self, node):
        if node is None:
            _LOG.debug('None')
            return None
        _LOG.debug('%s', _node_str(node))
        return super().visit(node)

    def visit_FileAST(self, node) -> typed_ast3.Module:  # pylint: disable=invalid-name
        ext = [self.visit(subnode) for subnode in node.ext]
        _ = self.visit(node.coord)
        module = typed_ast3.Module(body=fix_stmts_in_body(ext), type_ignores=[])
        return module

    def visit_FuncDef(self, node) -> typed_ast3.FunctionDef:  # pylint: disable=invalid-name
        """Transform FuncDef."""
        assert node.decl is not None
        name, args, return_type = self.visit(node.decl)
        param_decls = self.visit(node.param_decls)
        if param_decls is not None:
            raise NotImplementedError(_node_debug(node.param_decls), str(param_decls))
        body = self.visit(node.body)
        assert isinstance(body, list) and body
        _ = self.visit(node.coord)
        funcdef = typed_ast3.FunctionDef(name=name, args=args, body=fix_stmts_in_body(body),
                                         decorator_list=[], returns=return_type)
        return funcdef

    def visit_FuncDecl(  # pylint: disable=invalid-name
            self, node) -> t.Tuple[str, typed_ast3.arguments, typed_ast3.AST]:
        """Return a tuple: function name, its declared arguments and its return type"""
        args = self.visit(node.args)
        assert isinstance(args, typed_ast3.arguments)
        name, return_type = self.visit(node.type)
        assert isinstance(name, str)
        assert isinstance(return_type, typed_ast3.AST)
        # if type_ is not None:
        #    raise NotImplementedError(_node_debug(node.type), str(type_))
        _ = self.visit(node.coord)
        return name, args, return_type

    def visit_ParamList(self, node) -> typed_ast3.arguments:  # pylint: disable=invalid-name
        """Transform ParamList."""
        params = [self.visit(subnode) for subnode in node.params]
        # assert all(isinstance(param, tuple) for param in params), params
        # params = [typed_ast3.arg(arg=param[0], annotation=param[1]) for param in params]
        assert all(isinstance(param, typed_ast3.AnnAssign) for param in params), params
        assert all(isinstance(param.target, typed_ast3.Name) for param in params), params
        params = [typed_ast3.arg(arg=param.target.id, annotation=param.annotation)
                  for param in params]
        _ = self.visit(node.coord)
        return typed_ast3.arguments(args=params, vararg=None, kwonlyargs=[], kwarg=None,
                                    defaults=[], kw_defaults=[])

    def visit_Return(self, node) -> typed_ast3.Return:  # pylint: disable=invalid-name
        expr = self.visit(node.expr)
        assert isinstance(expr, typed_ast3.AST)
        _ = self.visit(node.coord)
        return typed_ast3.Return(value=expr)

    def visit_For(self, node) -> typed_ast3.For:  # pylint: disable=invalid-name
        """Transform For(init, cond, next, stmt: list, coord: t.Optional[Coord])."""
        init = self.visit(node.init)
        assert isinstance(init, typed_ast3.Assign)
        assert len(init.targets) == 1
        target = init.targets[0]
        begin = init.value
        assert isinstance(target, typed_ast3.Name)
        cond = self.visit(node.cond)
        assert isinstance(cond, typed_ast3.Compare)
        assert isinstance(cond.left, typed_ast3.Name)
        assert len(cond.ops) == 1
        assert isinstance(cond.ops[0], typed_ast3.Lt)
        assert len(cond.comparators) == 1
        end = cond.comparators[0]
        assert cond.left.id == target.id
        next_ = self.visit(node.next)
        assert isinstance(next_, typed_ast3.AugAssign)
        step = next_.value
        assert isinstance(next_.op, typed_ast3.Add)
        assert isinstance(step, typed_ast3.Num)
        iter_ = make_range_call(begin, end, step)
        stmt = self.visit(node.stmt)
        assert stmt is not None
        if not isinstance(stmt, list):
            stmt = [stmt]
        _ = self.visit(node.coord)
        return typed_ast3.For(target=target, iter=iter_, body=fix_stmts_in_body(stmt), orelse=[])

    def visit_If(self, node):  # pylint: disable=invalid-name
        """Transform If(cond, iftrue, iffalse, coord: t.Optional[Coord])."""
        cond = self.visit(node.cond)
        iftrue = self.visit(node.iftrue)
        if iftrue is not None:
            if not isinstance(iftrue, list):
                iftrue = [iftrue]
            iftrue = fix_stmts_in_body(iftrue)
        iffalse = self.visit(node.iffalse)
        if iffalse is None:
            iffalse = []
        else:
            if not isinstance(iffalse, list):
                iffalse = [iffalse]
            iffalse = fix_stmts_in_body(iffalse)
        _ = self.visit(node.coord)
        return typed_ast3.If(test=cond, body=iftrue, orelse=iffalse)

    def visit_Compound(self, node):  # pylint: disable=invalid-name
        """Transform Compound."""
        block_items = [self.visit(subnode) for subnode in node.block_items]
        _ = self.visit(node.coord)
        return fix_stmts_in_body(block_items)

    def visit_BinaryOp(self, node):  # pylint: disable=invalid-name
        """Transform BinaryOp."""
        op_type, op_ = C_BINARY_OPERATORS_TO_PYTHON[node.op]
        left = self.visit(node.left)
        right = self.visit(node.right)
        _ = self.visit(node.coord)
        if op_type is typed_ast3.BinOp:
            return op_type(left=left, op=op_(), right=right)
        if op_type is typed_ast3.Compare:
            return op_type(left=left, ops=[op_()], comparators=[right])
        return self.generic_visit(node)

    def visit_UnaryOp(self, node):  # pylint: disable=invalid-name
        """Transform UnaryOp."""
        op_type, op_ = C_UNARY_OPERATORS_TO_PYTHON[node.op]
        expr = self.visit(node.expr)
        _ = self.visit(node.coord)
        if op_type is typed_ast3.Call:
            return op_type(func=typed_ast3.Name(id=op_, ctx=typed_ast3.Load()), args=[expr],
                           keywords=[])
        if op_type is typed_ast3.AugAssign:
            return op_type(target=expr, op=op_(), value=typed_ast3.Num(n=1))
            # raise NotImplementedError()
        return op_type(op=op_, operand=expr)

    def visit_Cast(self, node):  # pylint: disable=invalid-name
        """Transform C cast into cast() function call."""
        to_type = self.visit(node.to_type)
        expr = self.visit(node.expr)
        _ = self.visit(node.coord)
        return typed_ast3.Call(func=typed_ast3.Name(id='cast', ctx=typed_ast3.Load()), args=[expr],
                               keywords=[typed_ast3.keyword(arg='type', value=to_type)])

    def visit_ID(self, node):  # pylint: disable=invalid-name
        name = node.name
        _ = self.visit(node.coord)
        return typed_ast3.Name(id=name, ctx=typed_ast3.Load())

    def visit_Constant(self, node):  # pylint: disable=invalid-name
        """Transform Constant into Num or Str."""
        type_ = node.type
        value = node.value
        _ = self.visit(node.coord)
        if type_ in ('int',):
            return typed_ast3.Num(int(value))
        if type_ in ('string',):
            assert value[0] == '"' and value[-1] == '"', value
            return typed_ast3.Str(value[1:-1])
        return self.generic_visit(node)

    def visit_Assignment(  # pylint: disable=invalid-name
            self, node) -> t.Union[typed_ast3.Assign, typed_ast3.AugAssign]:
        """Transform Assignment."""
        op_type, op_ = C_ASSIGNMENT_OPERATORS_TO_PYTHON[node.op]
        lvalue = self.visit(node.lvalue)
        assert isinstance(lvalue, typed_ast3.AST)
        rvalue = self.visit(node.rvalue)
        assert isinstance(rvalue, typed_ast3.AST)
        _ = self.visit(node.coord)
        if op_type is typed_ast3.Assign:
            return op_type(targets=[lvalue], value=rvalue, type_comment=None)
        return op_type(target=lvalue, op=op_(), value=rvalue)

    def visit_Decl(self, node) -> t.Union[typed_ast3.AnnAssign,  # pylint: disable=invalid-name
                                          t.Tuple[str, typed_ast3.arguments, typed_ast3.AST]]:
        """Transform Decl."""
        name = node.name
        assert isinstance(name, str), type(name)
        quals = node.quals
        if quals:
            _LOG.error('ignoring unsupported C grammar: %s', quals)
        storage = [self.visit(subnode) for subnode in node.storage]
        if storage:
            raise NotImplementedError(_node_debug(node.storage), str(storage))
        funcspec = [self.visit(subnode) for subnode in node.funcspec]
        if funcspec:
            raise NotImplementedError(_node_debug(node.funcspec), str(funcspec))
        type_data = self.visit(node.type)
        assert isinstance(type_data, tuple)
        assert len(type_data) == DECL_DATA_LENGTHS[type(node.type)], (type(node.type), type_data)
        init = self.visit(node.init)
        if init is not None:
            assert isinstance(node.type, INITIALIZABLE_DECLARATIONS)
            # assert isinstance(node.type, c_ast.TypeDecl), type(node.type)
            # raise NotImplementedError(_node_debug(node.init), str(init))
        bitsize = self.visit(node.bitsize)
        if bitsize is not None:
            raise NotImplementedError(_node_debug(node.bitsize), str(bitsize))
        _ = self.visit(node.coord)
        if init is not None or isinstance(node.type, INITIALIZABLE_DECLARATIONS):
            name_, type_ = type_data
            assert name_ == name
            return typed_ast3.AnnAssign(target=typed_ast3.Name(id=name_, ctx=typed_ast3.Store()),
                                        annotation=type_, value=init, simple=1)
        if isinstance(node.type, (c_ast.FuncDecl,)):
            return type_data
        return self.generic_visit(node)

    def visit_TypeDecl(self, node) -> t.Tuple[str, typed_ast3.Name]:  # pylint: disable=invalid-name
        """Return a tuple: identifier and its type."""
        declname = node.declname
        assert declname is None or isinstance(declname, str)
        quals = node.quals
        type_ = self.visit(node.type)
        assert isinstance(type_, typed_ast3.Name), type(type_)
        for qual in quals:
            assert isinstance(qual, str)
            type_ = typed_ast3.Subscript(
                value=typed_ast3.Attribute(value=typed_ast3.Name(id='st', ctx=typed_ast3.Load()),
                                           attr=qual.title(), ctx=typed_ast3.Load()),
                slice=typed_ast3.Index(value=type_), ctx=typed_ast3.Load())
        _ = self.visit(node.coord)
        return declname, type_

    def visit_IdentifierType(self, node) -> typed_ast3.Name:  # pylint: disable=invalid-name
        """Transform IdentifierType(names: t.List[str], coord: t.Optional[Coord])."""
        names = node.names
        assert len(names) == 1, names
        name = names[0]
        assert isinstance(name, str)
        _ = self.visit(node.coord)
        return typed_ast3.Name(id=name, ctx=typed_ast3.Load())

    def visit_ArrayDecl(  # pylint: disable=invalid-name
            self, node) -> t.Tuple[str, typed_ast3.Subscript]:
        """Return tuple of: name, st.ndarray[..., ...] for given array type information."""
        name, type_ = self.visit(node.type)
        assert isinstance(name, str)
        assert isinstance(type_, typed_ast3.AST)
        dim = self.visit(node.dim)
        if dim is not None:
            raise NotImplementedError(_node_debug(node.dim), str(dim))
        dim_quals = [self.visit(subnode) for subnode in node.dim_quals]
        if dim_quals:
            raise NotImplementedError(_node_debug(node.dim_quals), str(dim_quals))
        _ = self.visit(node.coord)
        return name, typed_ast3.Subscript(
            value=typed_ast3.Attribute(value=typed_ast3.Name(id='st', ctx=typed_ast3.Load()),
                                       attr='ndarray', ctx=typed_ast3.Load()),
            slice=typed_ast3.ExtSlice(dims=[
                typed_ast3.Index(value=typed_ast3.Ellipsis()),
                typed_ast3.Index(value=type_)  # ,
                # typed_ast3.Index(value=typed_ast3.Tuple(n=-1))
                ]),
            ctx=typed_ast3.Load())

    def visit_ArrayRef(self, node):  # pylint: disable=invalid-name
        name = self.visit(node.name)
        subscript = self.visit(node.subscript)
        _ = self.visit(node.coord)
        return typed_ast3.Subscript(value=name, slice=typed_ast3.Index(subscript),
                                    ctx=typed_ast3.Load())

    def visit_PtrDecl(self, node):  # pylint: disable=invalid-name
        """Return st.Pointer[...] for given pointer type."""
        quals = node.quals
        if quals:
            _LOG.error('ignoring unsupported C grammar: %s', quals)
        name, type_ = self.visit(node.type)
        assert name is None or isinstance(name, str)
        assert isinstance(type_, typed_ast3.AST), type(type_)
        _ = self.visit(node.coord)
        # assert type_ is not None, _node_str(node)
        return name, typed_ast3.Subscript(
            value=typed_ast3.Attribute(value=typed_ast3.Name(id='st', ctx=typed_ast3.Load()),
                                       attr='Pointer', ctx=typed_ast3.Load()),
            slice=typed_ast3.Index(value=type_), ctx=typed_ast3.Load())

    def visit_FuncCall(self, node) -> typed_ast3.Call:  # pylint: disable=invalid-name
        """Return a call."""
        name = self.visit(node.name)
        assert isinstance(name, typed_ast3.Name)
        args = self.visit(node.args)
        _ = self.visit(node.coord)
        return typed_ast3.Call(func=name, args=args, keywords=[])

    def visit_ExprList(self, node) -> t.List[typed_ast3.AST]:  # pylint: disable=invalid-name
        """Return raw list of transformed expressions."""
        exprs = [self.visit(subnode) for subnode in node.exprs]
        assert all(isinstance(expr, typed_ast3.AST) for expr in exprs)
        _ = self.visit(node.coord)
        return exprs

    def visit_Typename(self, node):  # pylint: disable=invalid-name
        """Transform Typename."""
        name = self.visit(node.name)
        assert name is None or isinstance(name, typed_ast3.Name), type(name)
        if name is not None:
            raise NotImplementedError(_node_debug(node.name), str(name))
        quals = node.quals
        if quals:
            _LOG.error('ignoring unsupported C grammar: %s', quals)
        name_, type_ = self.visit(node.type)
        assert name_ is None, type(name_)
        assert isinstance(type_, typed_ast3.AST), type(type_)
        _ = self.visit(node.coord)
        return type_

    def visit_(self, node):  # pylint: disable=invalid-name
        """Transform ."""
        return

    def visit_Coord(self, node) -> tuple:  # pylint: disable=invalid-name
        """Transform Coord(file: str, line: int, column: int)."""
        return {'path': node.file, 'lineno': node.line, 'col': node.column}

    def generic_visit(self, node):
        raise NotImplementedError('{} cannot be processed'.format(_node_str(node)))


class CAstGeneralizer(AstGeneralizer):

    """Generalize AST obtained from pycparser."""

    def __init__(self):
        super().__init__(Language.find('C11'))

    def generalize(self, syntax):
        assert isinstance(syntax, c_ast.FileAST)
        backend = CAstGeneralizerBackend()
        general_ast = backend.visit(syntax)
        return general_ast
