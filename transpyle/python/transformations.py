"""Preliminary implementation of inlining."""

import collections.abc
import copy
import functools
import logging
import typing as t

import horast
import horast.nodes as horast_nodes
import static_typing as st
import typed_ast.ast3 as typed_ast3
import typed_astunparse

_LOG = logging.getLogger(__name__)

VALID_CONTEXTS = {
    typed_ast3.For: ('body', list),
    typed_ast3.FunctionDef: ('body', list),
    typed_ast3.Expr: ('value', typed_ast3.AST)}

VALID_CONTEXTS_TUPLE = tuple(VALID_CONTEXTS.keys())


def _flatten_sequence(sequence: t.MutableSequence[t.Any]) -> None:
    assert isinstance(sequence, collections.abc.MutableSequence)
    for i, elem in enumerate(sequence):
        if isinstance(elem, collections.abc.Sequence):
            for value in reversed(elem):
                sequence.insert(i, value)
            del sequence[i + len(elem)]


def flatten_syntax(syntax: t.Union[typed_ast3.AST, list]):
    if isinstance(syntax, (typed_ast3.Module, typed_ast3.FunctionDef, typed_ast3.ClassDef,
                           typed_ast3.For, typed_ast3.While, typed_ast3.If, typed_ast3.With,
                           typed_ast3.Try, typed_ast3.ExceptHandler,
                           typed_ast3.AsyncFunctionDef, typed_ast3.AsyncFor, typed_ast3.AsyncWith)):
        _flatten_sequence(syntax.body)
        for node in syntax.body:
            flatten_syntax(node)
    if isinstance(syntax, (typed_ast3.For, typed_ast3.While, typed_ast3.If, typed_ast3.Try,
                           typed_ast3.AsyncFor)):
        _flatten_sequence(syntax.orelse)
        for node in syntax.orelse:
            flatten_syntax(node)
    if isinstance(syntax, typed_ast3.Try):
        # flatten_sequence(syntax.handlers)
        for node in syntax.handlers:
            flatten_syntax(node)
        _flatten_sequence(syntax.finalbody)
        for node in syntax.finalbody:
            flatten_syntax(node)


class Replacer(st.ast_manipulation.RecursiveAstTransformer[typed_ast3]):

    def __init__(self, replacer):
        super().__init__()
        self._replacer = replacer

    def visit_node(self, node):
        return self._replacer(node)

    def __repr__(self):
        return 'Replacer({})'.format(self._replacer)


class ReturnFinder(st.ast_manipulation.RecursiveAstVisitor[typed_ast3]):

    def __init__(self):
        super().__init__()
        self.found = []

    def visit_node(self, node):
        if isinstance(node, typed_ast3.Return):
            self.found.append(node)


def replace_name(arg, value, name):
    if isinstance(name, typed_ast3.Name) and name.id == arg:
        return value
    return name


def create_name_replacers(values, replacements):
    args_mapping = {arg: value for arg, value in zip(values, replacements)}
    return [Replacer(functools.partial(replace_name, arg, value))
            for arg, value in args_mapping.items()]


def convert_return_to_assign(target, return_statement):
    if isinstance(return_statement, typed_ast3.Return):
        return typed_ast3.Assign(targets=[target], value=return_statement.value)
    return return_statement


class CallInliner(st.ast_manipulation.RecursiveAstTransformer[typed_ast3]):

    def __init__(self, inlined_function: st.nodes.StaticallyTypedFunctionDef[typed_ast3],
                 verbose: bool = True):
        super().__init__(fields_first=False)
        assert isinstance(inlined_function, typed_ast3.FunctionDef), type(inlined_function)
        assert inlined_function.body

        decorators = inlined_function.decorator_list
        if decorators:
            raise NotImplementedError('inlining with decorators not supported')

        arguments = inlined_function.args
        if arguments.vararg is not None or arguments.kwarg is not None:
            raise NotImplementedError('inlining of functions with *args or **kwargs not supported')
        if arguments.kwonlyargs or arguments.kw_defaults:
            raise NotImplementedError('only simple function definitions are currently supported')

        if arguments.defaults:
            _LOG.warning('default values for inlined function parameters will be ignored!')

        self._inlined_function = inlined_function
        self._inlined_args = [arg.arg for arg in inlined_function.args.args]
        self._verbose = verbose

        self._valid_inlining_contexts = {typed_ast3.Return}

        last_statement = self._inlined_function.body[-1]
        return_finder = ReturnFinder()
        return_finder.visit(self._inlined_function)
        _LOG.warning('last statement is: %s', last_statement)
        if len(self._inlined_function.body) == 1 and isinstance(last_statement, typed_ast3.Return):
            self._valid_inlining_contexts |= {t.Any}
        if not return_finder.found:
            self._valid_inlining_contexts |= {typed_ast3.Assign, typed_ast3.AnnAssign,
                                              typed_ast3.Expr}
        elif len(return_finder.found) == 1 and return_finder.found[0] is last_statement:
            self._valid_inlining_contexts |= {typed_ast3.Assign, typed_ast3.AnnAssign}

        _LOG.warning('function %s can only be inlined when in %s',
                     self._inlined_function.name, self._valid_inlining_contexts)

    def _inline_call_in_return(self, return_stmt):
        call = return_stmt.value
        assert self._is_valid_target_for_inlining(call)

        replacers = []
        replacers += create_name_replacers(self._inlined_args, call.args)

        inlined = self._inline_call(call, replacers)
        last_statement = inlined[-2] if self._verbose \
            else (inlined[-1] if isinstance(inlined, list) else inlined)
        if not isinstance(last_statement, typed_ast3.Return):
            if not isinstance(inlined, list):
                inlined = [inlined]
            inlined += [typed_ast3.Return(value=None)]
        return inlined

    def _inline_call_in_assign(self, assign):
        call = assign.value
        assert self._is_valid_target_for_inlining(call)
        assert isinstance(assign, typed_ast3.AnnAssign) or len(assign.targets) == 1

        target = getattr(assign, 'target', getattr(assign, 'targets', [None])[0])
        return_replacer = Replacer(functools.partial(convert_return_to_assign, target))

        replacers = []
        replacers += create_name_replacers(self._inlined_args, call.args)
        replacers += [return_replacer]

        return self._inline_call(call, replacers)

    def _inline_call_in_expr(self, expr):
        call = expr.value
        assert self._is_valid_target_for_inlining(call)

        replacers = []
        replacers += create_name_replacers(self._inlined_args, call.args)

        return self._inline_call(call, replacers)

    def _inline_call(self, call, replacers):
        # template_code = '''for dummy_variable in (0,):\n    pass'''
        # inlined_call = typed_ast3.parse(template_code).body[0]
        call_code = typed_astunparse.unparse(call).strip()
        inlined_statements = []
        if self._verbose:
            inlined_statements.append(horast_nodes.Comment(
                value=typed_ast3.Str(s=' inlined {}'.format(call_code)), eol=False))
        for stmt in self._inlined_function.body:
            stmt = st.augment(copy.deepcopy(stmt))
            for replacer in replacers:
                stmt = replacer.visit(stmt)
            inlined_statements.append(stmt)
        if self._verbose:
            inlined_statements.append(horast_nodes.Comment(
                value=typed_ast3.Str(s=' end of inlined {}'.format(call_code)), eol=False))
        _LOG.warning('inlining a call %s using replacers %s', call_code, replacers)
        # inlined_call.body = scope
        # return st.augment(inlined_call)
        assert inlined_statements
        if len(inlined_statements) == 1:
            return inlined_statements[0]
        return inlined_statements

    def visit(self, node):
        node = super().visit(node)
        flatten_syntax(node)
        return node

    def generic_visit(self, node):
        """Copied implementation from parent class - get rid of it at some point."""
        if not self._fields_first:
            _LOG.debug('visiting node %s', node)
            node = self.visit_node(node)
            if not hasattr(node, '_fields'):
                return node
        _LOG.debug('visiting all fields of node %s', node)
        for name, value in typed_ast3.iter_fields(node):
            setattr(node, name, self.generic_visit_field(node, name, value))
        if self._fields_first:
            _LOG.debug('visiting node %s', node)
            node = self.visit_node(node)
        return node

    def _is_target_for_inlining(self, call) -> bool:
        return isinstance(call, typed_ast3.Call) and isinstance(call.func, typed_ast3.Name) \
            and call.func.id == self._inlined_function.name

    def _is_valid_target_for_inlining(self, call) -> bool:
        if call.keywords:
            raise NotImplementedError('currently only simple calls can be inlined')
        if len(self._inlined_args) != len(call.args):
            raise ValueError(
                'Inlined function has {} parameters: {}, but target call has {} arguments: {}.'
                .format(len(self._inlined_args), self._inlined_args, len(call.args), call.args))
        return True

    def visit_node(self, node):
        # _LOG.warning('visiting %s', node)
        if isinstance(node, typed_ast3.Return) and self._is_target_for_inlining(node.value):
            return self._inline_call_in_return(node)
        if isinstance(node, (typed_ast3.Assign, typed_ast3.AnnAssign)) \
                and self._is_target_for_inlining(node.value):
            if typed_ast3.Assign not in self._valid_inlining_contexts:
                raise NotImplementedError('{} cannot be inlined inside {}'
                                          ' -- return supported only at the end of the function',
                                          self._inlined_function.name, type(node))
            return self._inline_call_in_assign(node)
        if isinstance(node, typed_ast3.Expr) and self._is_target_for_inlining(node.value):
            if typed_ast3.Expr not in self._valid_inlining_contexts:
                raise NotImplementedError('{} cannot be inlined inside {}'
                                          ' -- returns not supported',
                                          self._inlined_function.name, type(node))
            return self._inline_call_in_expr(node)
        if self._is_target_for_inlining(node):
            if t.Any not in self._valid_inlining_contexts:
                raise NotImplementedError('{} cannot be inlined in arbitrary context'
                                          ' -- only one-liners are supported')
            replacers = create_name_replacers(self._inlined_args, node.args)
            replacers.append(Replacer(lambda return_: return_.value
                                      if isinstance(return_, typed_ast3.Return) else return_))
            return self._inline_call(node, replacers)
        return node

    def visit_field(self, node, name: str, value: t.Any):
        # _LOG.warning('visiting %s=%s in %s', name, value, node)
        return value


def inline_calls(target: typed_ast3.FunctionDef, inlined_function: typed_ast3.FunctionDef,
                 *args, **kwargs) -> typed_ast3.FunctionDef:
    if not isinstance(target, st.nodes.StaticallyTypedFunctionDef[typed_ast3]):
        target = st.augment(target)
    if not isinstance(inlined_function, st.nodes.StaticallyTypedFunctionDef[typed_ast3]):
        inlined_function = st.augment(inlined_function)
    call_inliner = CallInliner(inlined_function, *args, **kwargs)
    target = call_inliner.visit(target)
    return target
