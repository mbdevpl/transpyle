"""Transformer of Fortran AST into Python AST."""

import ast
import functools
import itertools
import logging
import re
import typing as t
import xml.etree.ElementTree as ET

import horast
import horast.nodes as horast_nodes
import numpy as np
import static_typing as st
import typed_ast.ast3 as typed_ast3
import typed_astunparse

from ..pair import \
    make_expression_from_slice, make_numpy_constructor, make_st_ndarray, fix_stmts_in_body, \
    separate_args_and_keywords
from ..general.exc import ContinueIteration
from ..general.misc import flatten_sequence
from ..general import Language, XmlAstGeneralizer
from .definitions import \
    FORTRAN_PYTHON_TYPE_PAIRS, FORTRAN_PYTHON_OPERATORS, INTRINSICS_FORTRAN_TO_PYTHON, \
    INTRINSICS_SPECIAL_CASES

_LOG = logging.getLogger(__name__)

FORTRAN_PYTHON_FORMAT_SPEC = {
    'A': str,
    'I': int}


class FortranAstGeneralizer(XmlAstGeneralizer):

    """Transform Fortran AST in XML format into typed Python AST.

    The Fortran AST in XML format is provided by XML output generator for Open Fortran Parser.

    Typed Python AST is provided by typed-ast package.
    """

    def __init__(self, split_declarations: bool = True):
        super().__init__(Language.find('Fortran 2008'))
        self._split_declarations = split_declarations
        self._now_parsing_file = False

    def generalize(self, syntax: ET.Element):
        self._now_parsing_file = False
        generalized = super().generalize(syntax)
        return st.augment(generalized, eval_=False, locals_={'np': np, 'st': st})

    def _ofp(self, node: ET.Element):
        assert len(node) == 1
        return self.transform_one(node[0])

    def _file(self, node: ET.Element) -> t.Union[typed_ast3.Module, typed_ast3.Expr]:
        if not self._now_parsing_file:
            self._now_parsing_file = True
            body = self.transform_all_subnodes(node, ignored={'start-of-file', 'end-of-file'})
            self._now_parsing_file = False
            body = self.import_statements + body
        else:
            return typed_ast3.Expr(value=typed_ast3.Call(
                func=typed_ast3.Name(id='print', ctx=typed_ast3.Load()),
                args=[typed_ast3.Str(s='file'), typed_ast3.Str(s=node.attrib['path'])],
                keywords=[]))
        return typed_ast3.Module(body=body, type_ignores=[])

    def _comment(self, node: ET.Element) -> horast_nodes.Comment:
        comment = node.attrib['text']
        if not comment or comment[0] not in ('!', 'c', 'C'):
            raise SyntaxError('comment token {} has unexpected prefix'.format(repr(comment)))
        comment = comment[1:]
        return horast_nodes.Comment(value=typed_ast3.Str(s=comment), eol=False)

    def _directive(self, node) -> horast_nodes.Comment:
        directive = node.attrib['text']
        if not directive or directive[0] not in ('#',):
            raise SyntaxError('directive token {} has unexpected prefix'.format(repr(directive)))
        directive = directive[1:]
        directive_ = horast_nodes.Comment(value=typed_ast3.Str(s=directive), eol=False)
        directive_.fortran_metadata = {'is_directive': True}
        return directive_

    def _module(self, node: ET.Element):
        module = typed_ast3.parse('''if __name__ == '__main__':\n    pass''')
        body = self.transform_all_subnodes(self.get_one(node, './body'))
        conditional = module.body[0]
        conditional.body = body
        members_node = node.find('./members')
        if members_node is None:
            return conditional
        members = self.transform_all_subnodes(members_node)
        if not members:
            members = [typed_ast3.Pass()]
        clsdef = typed_ast3.ClassDef(
            name=node.attrib['name'], bases=[], keywords=[], body=members, decorator_list=[])
        return [conditional, clsdef]
        # _LOG.warning('%s', ET.tostring(node).decode().rstrip())
        # raise NotImplementedError('not implemented handling of:\n{}'
        #                          .format(ET.tostring(node).decode().rstrip()))

    def _function(self, node: ET.Element):
        arguments = self.transform_one(self.get_one(node, './header/names'))
        body = self.transform_all_subnodes(self.get_one(node, './body'))
        for i, stmt in enumerate(body):
            stmt = ast.fix_missing_locations(stmt)
            stmt = typed_ast3.fix_missing_locations(stmt)
            try:
                pass
                # stmt = st.augment(stmt, eval_=False)  # TODO: requires static_typing upgrades!
            except TypeError as err:
                raise RuntimeError(horast.dump(stmt)) from err
            except AttributeError as err:
                raise RuntimeError(horast.dump(stmt)) from err
            if isinstance(stmt, st.nodes.declaration.StaticallyTypedDeclaration[typed_ast3]):
                _LOG.warning('declaration in function')
            body[i] = stmt

        return typed_ast3.FunctionDef(
            name=node.attrib['name'], args=arguments, body=body, decorator_list=[],
            returns=typed_ast3.NameConstant(None), type_comment=None)

    def _subroutine(self, node: ET.Element) -> typed_ast3.FunctionDef:
        header_node = self.get_one(node, './header')
        arguments_node = header_node.find('./arguments')
        if arguments_node is None:
            arguments = typed_ast3.arguments(args=[], vararg=None, kwonlyargs=[], kwarg=None,
                                             defaults=[], kw_defaults=[])
        else:
            arguments = self.transform_one(arguments_node)
        body = self.transform_all_subnodes(self.get_one(node, './body'))
        function_def = typed_ast3.FunctionDef(
            name=node.attrib['name'], args=arguments, body=body, decorator_list=[],
            returns=typed_ast3.NameConstant(None), type_comment=None)
        members_node = node.find('./members')
        if members_node is not None:
            members = self.transform_all_subnodes(members_node, ignored={
                'internal-subprogram', 'internal-subprogram-part'})
            assert members
            function_def.fortran_metadata = {'contains': members}
        return function_def

    def _arguments(self, node: ET.Element) -> typed_ast3.arguments:
        return typed_ast3.arguments(
            args=self.transform_all_subnodes(node, ignored={
                'dummy-arg-list__begin', 'dummy-arg-list',
                'generic-name-list__begin', 'generic-name-list'}),
            vararg=None, kwonlyargs=[], kwarg=None, defaults=[], kw_defaults=[])

    def _argument(self, node: ET.Element) -> typed_ast3.arg:
        if 'name' not in node.attrib:
            raise SyntaxError(
                '"name" attribute not present in:\n{}'.format(ET.tostring(node).decode().rstrip()))
        values = self.transform_all_subnodes(node, skip_empty=False, ignored={
            'actual-arg', 'actual-arg-spec', 'dummy-arg'})
        if values:
            assert len(values) == 1
            _LOG.warning('generating invalid Python AST: keyword() in arguments()')
            return typed_ast3.keyword(arg=node.attrib['name'], value=values[0])
        return typed_ast3.arg(arg=node.attrib['name'], annotation=None)

    def _return(self, node: ET.Element) -> typed_ast3.Return:
        has_value = node.attrib['hasValue'] == 'true'
        if not has_value:
            return typed_ast3.Return(value=None)
        raise NotImplementedError(
            'not implemented handling of:\n{}'.format(ET.tostring(node).decode().rstrip()))

    def _stop(self, node: ET.Element) -> typed_ast3.Call:
        stop_code = node.attrib['code']
        args = []
        if stop_code:
            _LOG.warning('ignoring exit code in """%s"""', ET.tostring(node).decode().rstrip())
            # args.append(int(stop_code))
        return typed_ast3.Call(func=typed_ast3.Name(id='exit', ctx=typed_ast3.Load()),
                               args=args, keywords=[])

    def _program(self, node: ET.Element) -> typed_ast3.AST:
        module = typed_ast3.parse('''if __name__ == '__main__':\n    pass''')
        body = self.transform_all_subnodes(self.get_one(node, './body'))
        for i in range(len(body) - 1, -1, -1):
            if isinstance(body[i], list):
                sublist = body[i]
                del body[i]
                for elem in reversed(sublist):
                    body.insert(i, elem)
        conditional = module.body[0]
        conditional.body = body
        return conditional

    def _specification(self, node: ET.Element) -> t.List[typed_ast3.AST]:
        declarations = self.transform_all_subnodes(node, skip_empty=True, ignored={
            'declaration-construct', 'specification-part'})
        return declarations

    def _declaration(self, node: ET.Element) -> typed_ast3.AnnAssign:
        # if 'type' not in node.attrib:
        #    # return []  # TODO: TMP
        #    raise SyntaxError(
        #        '"type" attribute not present in:\n{}'.format(ET.tostring(node).decode().rstrip()))
        declaration_type = node.attrib.get('type', None)
        if declaration_type is None:
            pass
        elif declaration_type == 'implicit':
            return self._declaration_implicit(node)
        elif declaration_type == 'variable':
            return self._declaration_variable(node)
        # elif declaration_type == 'variable-dimensions':
        #    return self._declaration_variable_dimensions(node)
        elif declaration_type == 'parameter':
            return self._declaration_parameter(node)
        elif declaration_type == 'include':
            return self._declaration_include(node)
        elif declaration_type in ('variable-dimensions', 'data', 'external'):
            return typed_ast3.Expr(value=typed_ast3.Call(
                func=typed_ast3.Name(id='print', ctx=typed_ast3.Load()),
                args=[typed_ast3.Str(s='declaration'), typed_ast3.Str(s=node.attrib['type'])],
                keywords=[]))
        details = self.transform_all_subnodes(node, ignored={})
        return details
        # raise NotImplementedError(
        #    'not implemented handling of:\n{}'.format(ET.tostring(node).decode().rstrip()))

    def _declaration_implicit(self, node) -> typed_ast3.AnnAssign:
        subtype = node.attrib['subtype'].lower()
        if subtype == 'none':
            annotation = typed_ast3.NameConstant(value=None)
        elif subtype == 'some':
            base_type = self.transform_one(self.get_one(node, './type'))
            letter_ranges = self.transform_one(self.get_one(node, './letter-ranges'))
            letter_ranges = typed_ast3.Tuple(elts=letter_ranges, ctx=typed_ast3.Load())
            annotation = typed_ast3.Subscript(
                value=typed_ast3.Attribute(
                    value=typed_ast3.Name(id='Fortran', ctx=typed_ast3.Load()),
                    attr='TypeByNamePrefix', ctx=typed_ast3.Load()),
                slice=typed_ast3.Index(
                    value=typed_ast3.Tuple(elts=[base_type, letter_ranges], ctx=typed_ast3.Load()),
                    ctx=typed_ast3.Load()), ctx=typed_ast3.Load())
        else:
            raise SyntaxError('expecting only "none" or "some", but got "{}"'.format(subtype))
        implicit = typed_ast3.AnnAssign(
            target=typed_ast3.Name(id='implicit', ctx=typed_ast3.Store()), annotation=annotation,
            value=None, simple=True)
        implicit.fortran_metadata = {'is_declaration': True}
        return implicit

    def _letter_ranges(self, node) -> t.List[typed_ast3.Str]:
        return self.transform_all_subnodes(node, ignored={
            'letter-spec-list__begin', 'letter-spec-list'})

    def _letter_range(self, node) -> typed_ast3.Str:
        begin = node.attrib['begin']
        end = node.attrib['end']
        assert re.fullmatch('[a-zA-Z]', begin), begin
        assert re.fullmatch('[a-zA-Z]', end), end
        return typed_ast3.Str(s='[{}-{}]'.format(begin, end))

    def _declaration_variable(
            self, node: ET.Element) -> t.Union[
                typed_ast3.Assign, typed_ast3.AnnAssign, t.List[typed_ast3.Assign],
                t.List[typed_ast3.AnnAssign]]:
        """Reorganize data from multi-variable declaration into sequence of anotated assignments."""

        # variable names
        variables_and_values = self.transform_all_subnodes(
            self.get_one(node, './variables'), skip_empty=True,
            ignored={'entity-decl-list__begin', 'entity-decl-list'})
        if not variables_and_values:
            _LOG.error('%s', ET.tostring(node).decode().rstrip())
            raise SyntaxError('at least one variable expected in variables list')
        variables = [var for var, _ in variables_and_values]

        # base type of variables
        base_type = self.transform_one(self.get_one(node, './type'))

        # dimensionality information (only for array types)
        dimensions_node = node.find('./dimensions')
        variable_dimensions = [getattr(var, 'fortran_metadata', {}).get('dimensions', None)
                               for var in variables]
        has_variable_dimensions = any([_ is not None for _ in variable_dimensions])
        if has_variable_dimensions and not self._split_declarations:
            raise NotImplementedError('inline dimensions not implemented yet')
        if dimensions_node is not None and has_variable_dimensions:
            raise SyntaxError(
                'declaration dimension data as well as per-variable dimension data present')
        if dimensions_node is not None:
            dimensions = self.transform_one(dimensions_node)
            assert len(dimensions) >= 1
            self.ensure_import('static_typing', 'st')
            annotation = make_st_ndarray(base_type, dimensions)
            annotations = [annotation for _ in variables]
        elif has_variable_dimensions:
            self.ensure_import('static_typing', 'st')
            annotations = [base_type if _ is None else make_st_ndarray(base_type, _)
                           for _ in variable_dimensions]
        else:
            annotations = [base_type for _ in variables]

        # initial values
        if dimensions_node is not None:
            values = [None if val is None else make_numpy_constructor('array', val, base_type)
                      for _, val in variables_and_values]
        elif has_variable_dimensions:
            assert len(variables_and_values) == len(variable_dimensions)
            values = [None if val is None
                      else (val if dim is None else make_numpy_constructor('array', val, base_type))
                      for (_, val), dim in zip(variables_and_values, variable_dimensions)]
        else:
            values = [val for _, val in variables_and_values]

        metadata = {'is_declaration': True}
        intent_node = node.find('./intent')
        if intent_node is not None:
            metadata['intent'] = intent_node.attrib['type']

        attributes = ('allocatable', 'asynchronous', 'external', 'intrinsic', 'optional',
                      'parameter', 'pointer', 'protected', 'save', 'target', 'value', 'volatile')
        for attribute in attributes:
            if node.find('./attribute-{}'.format(attribute)) is not None:
                metadata['is_{}'.format(attribute)] = True

        if metadata:
            metadata_node = horast_nodes.Comment(
                value=typed_ast3.Str(s=' Fortran metadata: {}'.format(repr(metadata))), eol=False)

        _handled = {'variables', 'type', 'dimensions', 'intent'}
        extra_results = self.transform_all_subnodes(node, ignored={
            'type-declaration-stmt'} | _handled | {'attribute-{}'.format(_) for _ in attributes})
        if extra_results:
            _LOG.warning('ignoring additional information in the declaration:\n%s', extra_results)

        if not self._split_declarations:
            raise NotImplementedError()
        assignments = [typed_ast3.AnnAssign(target=var, annotation=ann, value=val, simple=True)
                       for var, ann, val in zip(variables, annotations, values)]
        if metadata:
            new_assignments = []
            for assignment in assignments:
                assignment.fortran_metadata = metadata
                new_assignments.append(assignment)
                new_assignments.append(metadata_node)
            assignments = new_assignments

        return assignments

    def _attr_spec(self, node: ET.Element):
        attr = node.attrib['attrKeyword'].lower()
        if attr in {'dimension', 'intent'}:
            raise ContinueIteration()
        self.no_transform(node)

    def _declaration_parameter(self, node: ET.Element):
        constants = self.transform_all_subnodes(
            self.get_one(node, './constants'), skip_empty=True, ignored={
                'named-constant-def-list__begin', 'named-constant-def-list'})
        assignments = []
        for constant, value in constants:
            assert isinstance(constant, typed_ast3.AST)
            assignment = typed_ast3.Assign(targets=[constant], value=value, type_comment=None)
            assignment.fortran_metadata = {'is_constant': True}
            assignments.append(assignment)
        return assignments

    def _constant(self, node: ET.Element) -> t.Tuple[typed_ast3.Name, t.Any]:
        values = self.transform_all_subnodes(node, ignored={'named-constant-def'})
        assert len(values) == 1
        value = values[0]
        name = typed_ast3.Name(id=node.attrib['name'], ctx=typed_ast3.Load())
        return name, value

    def _declaration_include(self, node: ET.Element) -> typed_ast3.Import:
        path_attrib = self.get_one(node, './file').attrib['path']
        self.ensure_import(path_attrib)
        return typed_ast3.Import(names=[typed_ast3.alias(name=path_attrib, asname=None)])

    def _label(self, node: ET.Element) -> typed_ast3.Num:
        return typed_ast3.Num(n=int(node.attrib['lbl']))

    def _format(self, node: ET.Element) -> t.Union[typed_ast3.AnnAssign, typed_ast3.JoinedStr]:
        value = self.transform_one(self.get_one(node, './format-items'))
        label_node = node.find('./label')
        if label_node is None:
            return value
        label = int(label_node.attrib['lbl'])
        var = typed_ast3.Name(id='format_label_{}'.format(label), ctx=typed_ast3.Store())
        annotation = typed_ast3.Str('Fortran label')
        format_ = typed_ast3.AnnAssign(target=var, annotation=annotation, value=value, simple=True)
        format_.fortran_metadata = {'is_format': True}
        return format_

    def _format_items(self, node) -> typed_ast3.JoinedStr:
        items = self.transform_all_subnodes(node, ignored={
            'format-item-list__begin', 'format-item-list'})
        return typed_ast3.JoinedStr(values=items)

    def _format_item(self, node) -> t.Union[typed_ast3.Str, typed_ast3.FormattedValue]:
        raw_item = node.attrib['descOrDigit']
        if raw_item[0] in ('"', "'"):
            return typed_ast3.Str(s=raw_item[1:-1])
        if raw_item[0] in FORTRAN_PYTHON_FORMAT_SPEC:
            assert len(raw_item) == 2, raw_item
            item = typed_ast3.Name(id=raw_item, ctx=typed_ast3.Load())
            return typed_ast3.FormattedValue(value=item, conversion=-1, format_spec=None)
        raise NotImplementedError(
            'not implemented handling of:\n{}'.format(ET.tostring(node).decode().rstrip()))

    def _use(self, node: ET.Element):
        name = node.attrib['name']
        only_node = node.find('./only')
        if only_node is None:
            return typed_ast3.Import(names=[typed_ast3.alias(name=name, asname=None)])
        uses = self.transform_all_subnodes(only_node,
                                           ignored={'only-list__begin', 'only', 'only-list'})
        return typed_ast3.ImportFrom(
            module=name, names=[typed_ast3.alias(name=use.id, asname=None) for use in uses],
            level=0)

    def _loop(self, node: ET.Element):
        if node.attrib['type'] == 'do':
            return self._loop_do(node)
        elif node.attrib['type'] == 'implied-do':
            return self._loop_implied_do(node)
        elif node.attrib['type'] == 'do-while':
            return self._loop_do_while(node)
        elif node.attrib['type'] == 'do-label':
            return self._loop_do_while(node, condition=typed_ast3.NameConstant(value=True))
        elif node.attrib['type'] == 'forall':
            return self._loop_forall(node)
        else:
            raise NotImplementedError(
                'not implemented handling of:\n{}'.format(ET.tostring(node).decode().rstrip()))

    def _loop_do(self, node: ET.Element) -> typed_ast3.For:
        index_variable = self.get_one(node, './header/index-variable')
        body_node = self.get_one(node, './body')
        target, iter_ = self._index_variable(index_variable)
        body = self.transform_all_subnodes(body_node, ignored={'block'})
        body = fix_stmts_in_body(body)
        return typed_ast3.For(target=target, iter=iter_, body=body, orelse=[])

    def _loop_implied_do(self, node: ET.Element) -> typed_ast3.ListComp:
        index_variable = self.get_one(node, './header/index-variable')
        body_node = self.get_one(node, './body')
        comp_target, comp_iter = self._index_variable(index_variable)
        expressions = self.transform_all_subnodes(body_node, ignored={})
        assert len(expressions) > 0
        elt = expressions[0] if len(expressions) == 1 \
            else typed_ast3.Tuple(elts=expressions, ctx=typed_ast3.Load())
        generator = typed_ast3.comprehension(
            target=comp_target, iter=comp_iter, ifs=[], is_async=0)
        return typed_ast3.ListComp(elt=elt, generators=[generator])
        # target=target, iter=iter_, body=body, orelse=[])

    def _loop_do_while(self, node: ET.Element,
                       condition: typed_ast3.AST = None) -> typed_ast3.While:
        try:
            header = self.transform_all_subnodes(self.get_one(node, './header'))
            assert len(header) == 1
            assert condition is None
            condition = header[0]
        except SyntaxError:
            if condition is None:
                raise
        body = self.transform_all_subnodes(self.get_one(node, './body'), ignored={'block'})
        return typed_ast3.While(test=condition, body=body, orelse=[])

    def _loop_forall(self, node: ET.Element) -> typed_ast3.For:
        index_variables = self.get_one(node, './header/index-variables')
        outer_loop = None
        inner_loop = None
        for index_variable in index_variables.findall('./index-variable'):
            if not index_variable:
                continue  # TODO: this is just a duct tape
            target, iter_ = self._index_variable(index_variable)
            if outer_loop is None:
                outer_loop = typed_ast3.For(target=target, iter=iter_, body=[], orelse=[])
                inner_loop = outer_loop
                continue
            inner_loop.body = [typed_ast3.For(target=target, iter=iter_, body=[], orelse=[])]
            inner_loop = inner_loop.body[0]
        # inner_loop.body = [self.transform_one(self.get_one(node, './assignmet'))]
        inner_loop.body = self.transform_all_subnodes(self.get_one(node, './body'))
        return outer_loop

    def _index_variable(self, node: ET.Element) -> t.Tuple[typed_ast3.Name, typed_ast3.Call]:
        target = typed_ast3.Name(id=node.attrib['name'], ctx=typed_ast3.Load())
        lower_bound = node.find('./lower-bound')
        upper_bound = node.find('./upper-bound')
        step = node.find('./step')
        range_args = []
        if lower_bound is not None:
            args = self.transform_all_subnodes(lower_bound)
            assert len(args) == 1, args
            range_args.append(args[0])
        if upper_bound is not None:
            args = self.transform_all_subnodes(upper_bound)
            assert len(args) == 1, args
            range_args.append(typed_ast3.BinOp(
                left=args[0], op=typed_ast3.Add(), right=typed_ast3.Num(n=1)))
        if step is not None:
            args = self.transform_all_subnodes(step)
            assert len(args) == 1, args
            range_args.append(args[0])
        iter_ = typed_ast3.Call(
            func=typed_ast3.Name(id='range', ctx=typed_ast3.Load()),
            args=range_args, keywords=[])
        return target, iter_

    def _continue(self, node: ET.Element) -> typed_ast3.Pass:
        label_node = node.find('./label')
        label = None if label_node is None else self.transform_one(label_node)
        result = [typed_ast3.Pass()]
        if label is not None:
            cmnt = 'label: {}'.format(typed_astunparse.unparse(label).strip())
            result += [horast_nodes.Comment(value=typed_ast3.Str(s=cmnt), eol=True)]
        return result

    def _cycle(self, node: ET.Element) -> typed_ast3.Continue:
        return typed_ast3.Continue()

    def _exit(self, node: ET.Element) -> typed_ast3.Break:
        return typed_ast3.Break()

    def _goto_stmt(self, node):
        # TODO: make a better placeholder for goto
        return typed_ast3.Expr(value=typed_ast3.Call(
            func=typed_ast3.Name(id='print', ctx=typed_ast3.Load()),
            args=[typed_ast3.Str(s='goto'), typed_ast3.Str(s=node.attrib['target_label'])],
            keywords=[]))

    def _if(self, node: ET.Element):
        headers = self.get_all(node, './header')
        bodies = self.get_all(node, './body')
        outermost_if = None
        current_if = None
        for header, body in itertools.zip_longest(headers, bodies):
            if outermost_if is None:
                outermost_if = self._if_if(header, body)
                current_if = outermost_if
                continue
            assert current_if is not None
            if header is None:
                else_body = self._if_else(body)
                current_if.orelse += else_body
                current_if = None
            else:
                else_if = self._if_elif(header, body)
                current_if.orelse.append(else_if)
                current_if = else_if  # current_if.orelse[-1]
        return outermost_if

    def _if_if(self, header_node: ET.Element, body_node: ET.Element) -> typed_ast3.If:
        header = self.transform_all_subnodes(header_node, ignored={
            'executable-construct', 'execution-part-construct'})
        if len(header) != 1:
            raise SyntaxError('multiple headers {} in if:\n{}'.format(
                [typed_astunparse.unparse(_).rstrip() for _ in header],
                ET.tostring(header_node).decode().rstrip()))
        body = self._if_body(body_node)
        if_ = typed_ast3.If(test=header[0], body=body, orelse=[])
        return if_

    def _if_body(self, body_node: ET.Element) -> t.List[typed_ast3.AST]:
        body = self.transform_all_subnodes(body_node, skip_empty=True, ignored={'block'})
        flatten_sequence(body)
        for stmt in body:
            assert not isinstance(stmt, list), stmt
        return body

    def _if_elif(self, header_node: ET.Element, body_node: ET.Element) -> typed_ast3.If:
        assert header_node.attrib['type'] == 'else-if'
        assert body_node.attrib['type'] == 'else-if'
        return self._if_if(header_node, body_node)

    def _if_else(self, body_node: ET.Element) -> t.List[typed_ast3.AST]:
        assert body_node.attrib['type'] == 'else'
        return self._if_body(body_node)

    def _select(self, node: ET.Element):
        var = self.transform_all_subnodes(self.get_one(node, './header'), ignored={
            'executable-construct', 'execution-part-construct'})
        cases = self.transform_all_subnodes(self.get_one(node, './body'))
        assert cases, 'encountered select without cases'
        assert len(var) == 1, var
        var = var[0]
        items = []
        first_case = None
        prev_case = None
        for case in cases:
            if not isinstance(case, typed_ast3.If):
                if isinstance(case, list):
                    flatten_sequence(case)
                    items += case
                else:
                    assert isinstance(case, typed_ast3.AST), type(case)
                    items.append(case)
                _LOG.debug('accumulated %s', [horast.unparse(_) for _ in items])
                continue
            assert not isinstance(case.test, list), case.test
            if isinstance(case.test, typed_ast3.Tuple):
                op_ = typed_ast3.In()
            else:
                op_ = typed_ast3.Eq()
            case.test = typed_ast3.Compare(left=var, ops=[op_], comparators=[case.test])
            if items:
                _LOG.debug('prepending %s', [horast.unparse(_) for _ in items])
                case.body = items + case.body
                items = []
            if first_case is None:
                first_case = case
            if prev_case is not None:
                assert isinstance(case, typed_ast3.AST), type(case)
                prev_case.orelse.append(case)
            prev_case = case
        if items:
            prev_case.body += items
            _LOG.debug('appending %s', [horast.unparse(_) for _ in items])
        first_case.fortran_metadata = {'is_select': True}
        return first_case

    def _case(self, node: ET.Element):
        header_node = self.get_one(node, './header')
        body_node = self.get_one(node, './body')
        header = self.transform_all_subnodes(header_node, ignored={
            'executable-construct', 'execution-part-construct'})
        if len(header) > 1:
            _LOG.warning('many case values: %s',
                         [typed_astunparse.unparse(_).rstrip() for _ in header])
            header = [typed_ast3.Tuple(elts=header, ctx=typed_ast3.Load())]
        body = self._if_body(body_node)
        if_ = typed_ast3.If(test=header[0], body=body, orelse=[])
        return if_

    def _value_ranges(self, node: ET.Element):
        value_ranges = self.transform_all_subnodes(node, ignored={
            'case-value-range-list__begin', 'case-value-range', 'case-value-range-list'})
        value_ranges = [_ for _ in value_ranges if _ is not None]
        assert len(value_ranges) == int(node.attrib['count']), (value_ranges, node.attrib['count'])
        return value_ranges

    def _value_range(self, node: ET.Element):
        values = self.transform_all_subnodes(node, skip_empty=True, ignored={
            'case-value', 'case-value-range-suffix'})
        # self.no_transform(node)
        if not values:
            return None
        return values

    def _value(self, node: ET.Element):
        values = self.transform_all_subnodes(node)
        assert len(values) == 1, values
        return values[0]

    def _expressions(self, node: ET.Element) -> t.List[typed_ast3.AST]:
        return self.transform_all_subnodes(node, ignored={
            'allocate-object-list__begin', 'allocate-object-list',
            'allocation-list__begin', 'allocation-list'})

    def _expression(self, node) -> typed_ast3.AST:
        expression = self.transform_all_subnodes(node, ignored={
            'output-item', 'io-implied-do-object',
            'allocate-object', 'allocation'})
        if len(expression) != 1:
            raise NotImplementedError('exactly one output expected but {} found in:\n{}'.format(
                len(expression), ET.tostring(node).decode().rstrip()))
        return expression[0]

    def _statement(self, node: ET.Element):
        details = self.transform_all_subnodes(node, ignored={
            'action-stmt', 'executable-construct', 'execution-part-construct',
            'do-term-action-stmt',  # until do loop parsing implementation is changed
            'execution-part'})
        # if len(details) == 0:
        #    args = [
        #        typed_ast3.Str(s=ET.tostring(node).decode().rstrip()),
        #        typed_ast3.Num(n=len(node))]
        #    return [
        #        typed_ast3.Expr(value=typed_ast3.Call(
        #            func=typed_ast3.Name(id='print', ctx=typed_ast3.Load()),
        #            args=args, keywords=[])),
        #        typed_ast3.Pass()]

        # ast_module.FunctionDef, ast_module.AsyncFunctionDef, ast_module.ClassDef,
        # ast_module.Return, ast_module.Delete, ast_module.Assign, ast_module.AugAssign,
        # ast_module.AnnAssign, ast_module.For, ast_module.AsyncFor, ast_module.While,
        # ast_module.If, ast_module.With, ast_module.AsyncWith, ast_module.Raise, ast_module.Try,
        # ast_module.Assert, ast_module.Import, ast_module.ImportFrom, ast_module.Global,
        # ast_module.Nonlocal, ast_module.Expr, ast_module.Pass, ast_module.Break,
        # ast_module.Continue
        return [
            detail if isinstance(detail, (
                typed_ast3.Return, typed_ast3.Delete, typed_ast3.Assign, typed_ast3.AugAssign,
                typed_ast3.AnnAssign, typed_ast3.For, typed_ast3.While,
                typed_ast3.If, typed_ast3.With,
                typed_ast3.Assert,
                typed_ast3.Expr, typed_ast3.Pass, typed_ast3.Break,
                typed_ast3.Continue))
            else typed_ast3.Expr(value=detail)
            for detail in details]

    def _allocate(self, node: ET.Element) -> t.List[typed_ast3.Assign]:
        expressions = self.transform_one(self.get_one(node, './expressions'))
        assignments = []
        for expression in expressions:
            assert isinstance(expression, typed_ast3.Subscript), type(expression)
            var = expression.value
            sizes = make_expression_from_slice(expression.slice)
            if not isinstance(sizes, typed_ast3.Tuple):
                sizes = typed_ast3.Tuple(elts=[sizes], ctx=typed_ast3.Load())
            val = typed_ast3.Call(
                func=typed_ast3.Attribute(value=typed_ast3.Name(id='np', ctx=typed_ast3.Load()),
                                          attr='zeros', ctx=typed_ast3.Load()),
                args=[sizes], keywords=[typed_ast3.keyword(arg='dtype', value=typed_ast3.Attribute(
                    value=typed_ast3.Name(id='t', ctx=typed_ast3.Load()), attr='Any',
                    ctx=typed_ast3.Load()))])
            assert isinstance(var, typed_ast3.AST)
            assignment = typed_ast3.Assign(targets=[var], value=val, type_comment=None)
            assignment.fortran_metadata = {'is_allocation': True}
            assignments.append(assignment)
            assignments.append(horast_nodes.Comment(value=typed_ast3.Str(
                s=' Fortran metadata: {}'.format(repr(assignment.fortran_metadata))), eol=True))
        return assignments

    def _deallocate(self, node: ET.Element) -> typed_ast3.Delete:
        expressions = self.transform_one(self.get_one(node, './expressions'))
        targets = []
        for expression in expressions:
            assert isinstance(expression, typed_ast3.Name), type(expression)
            targets.append(expression)
        return typed_ast3.Delete(targets=targets)

    def _call(self, node: ET.Element) -> t.Union[typed_ast3.Call, typed_ast3.Assign]:
        called = self.transform_all_subnodes(node, ignored={'call-stmt'})
        if len(called) != 1:
            raise SyntaxError(
                'call statement must contain a single called object, not {}, like in:\n{}'.format(
                    [typed_astunparse.unparse(_).rstrip() for _ in called],
                    ET.tostring(node).decode().rstrip()))
        call = called[0]
        if not isinstance(call, typed_ast3.Call):
            name_node = node.find('./name')
            is_intrinsic = name_node.attrib['id'].lower() in self._intrinsics_converters \
                if name_node is not None else False
            if is_intrinsic:
                if isinstance(call, typed_ast3.Call):
                    call.fortran_metadata = {'is_procedure_call': True}
                return call
            _LOG.warning('called an ambiguous node:\n%s', ET.tostring(node).decode().rstrip())
            call = typed_ast3.Call(func=call, args=[], keywords=[])
        if isinstance(call.func, typed_ast3.Name) and call.func.id.startswith('MPI_'):
            call = self._transform_mpi_call(call)
        if isinstance(call, typed_ast3.Call):
            call.fortran_metadata = {'is_procedure_call': True}
        return call

    def _write(self, node) -> t.Union[typed_ast3.Expr, typed_ast3.Assign]:
        args = []
        written = []
        io_controls_node = node.find('./io-controls')
        if io_controls_node is not None:
            args = self.transform_one(io_controls_node)
        outputs_node = node.find('./outputs')
        if outputs_node is not None:
            written = self.transform_one(outputs_node)
        if len(written) > 1 or len(args) > 1:
            # file
            pass
        else:
            # string
            pass
        args += written
        args, keywords = separate_args_and_keywords(args)
        return typed_ast3.Expr(value=typed_ast3.Call(
            func=typed_ast3.Name(id='write', ctx=typed_ast3.Load()),
            args=args, keywords=keywords))

    def _read(self, node: ET.Element):
        file_handle = self._create_file_handle_var()
        io_controls = self.transform_one(self.get_one(node, './io-controls'))
        inputs = self.transform_one(self.get_one(node, './inputs'))
        for i, io_control in enumerate(list(io_controls)):
            if isinstance(io_control, typed_ast3.keyword):
                arg_name = io_control.arg.lower()
                if arg_name != 'unit':
                    continue
                file_handle.slice.value = io_controls.pop(i).value
                break
            file_handle.slice.value = io_controls.pop(i)
            break
        if io_controls:
            _LOG.warning(
                'ignoring remaining %i parameters of read call %s in"\n%s',
                len(io_controls), [typed_astunparse.unparse(_) for _ in io_controls],
                ET.tostring(node).decode().rstrip())
        assert all(isinstance(input_, typed_ast3.AST) for input_ in inputs), inputs
        return [
            typed_ast3.Assign(
                targets=[input_], value=typed_ast3.Call(
                    func=typed_ast3.Attribute(
                        value=file_handle, attr='read', ctx=typed_ast3.Load()),
                    args=[], keywords=[]),
                type_comment=None)
            for input_ in inputs]

    def _print(self, node):
        format_node = self.get_one(node, './print-format')
        format_ = None
        if format_node.attrib['type'] == 'label':
            format_ = self.transform_one(format_node)
        outputs_node = node.find('./outputs')
        args = []
        if outputs_node is not None:
            args = self.transform_one(outputs_node)
            assert all(not isinstance(_, typed_ast3.keyword) for _ in args), args
            if format_ is not None:
                if isinstance(format_, typed_ast3.Num):
                    name = 'format_label_{}'.format(format_.n)
                    value = typed_ast3.Name(id=name, ctx=typed_ast3.Load())
                elif isinstance(format_, typed_ast3.Str):
                    value = format_
                else:
                    raise NotImplementedError()
                args = [typed_ast3.Call(
                    func=typed_ast3.Attribute(value=value, attr='format', ctx=typed_ast3.Load()),
                    args=args, keywords=[])]
        # assert all(not isinstance(_, typed_ast3.keyword) for _ in args), args
        return typed_ast3.Expr(value=typed_ast3.Call(
            func=typed_ast3.Name(id='print', ctx=typed_ast3.Load()),
            args=args, keywords=[]))

    def _print_format(self, node: ET.Element) -> t.Union[None, typed_ast3.Num, typed_ast3.Str]:
        fmt = self.transform_all_subnodes(node, ignored={'format'})
        if not fmt:
            return None
        assert len(fmt) == 1, (len(fmt), fmt)
        assert isinstance(fmt[0], (typed_ast3.Num, typed_ast3.Str)), type(fmt[0])
        return fmt[0]

    def _io_controls(self, node: ET.Element):
        return self.transform_all_subnodes(node, skip_empty=True, ignored={
            'io-control-spec-list__begin', 'io-control-spec-list'})

    def _io_control(self, node) -> typed_ast3.AST:
        io_control = self.transform_all_subnodes(node, ignored={'io-control-spec'})
        arg_name = node.attrib['argument-name']
        if len(node) == 0 and not arg_name:
            return []  # TODO: TMP
        if len(io_control) == 0:
            assert arg_name == ''
            return typed_ast3.Ellipsis()  # TODO: TMP
        if len(io_control) != 1:
            raise NotImplementedError('exactly one I/O control expected but {} found in:\n{}'.
                                      format(len(io_control), ET.tostring(node).decode().rstrip()))
        if node.attrib['argument-name']:
            return typed_ast3.keyword(arg=arg_name, value=io_control[0])
        return io_control[0]

    def _outputs(self, node: ET.Element):
        return self.transform_all_subnodes(node, skip_empty=True, ignored={
            'output-item-list__begin', 'output-item-list'})

    def _output(self, node):
        output = self.transform_all_subnodes(node, ignored={'output-item'})
        if len(output) != 1:
            raise NotImplementedError('exactly one output expected but {} found in:\n{}'.format(
                len(output), ET.tostring(node).decode().rstrip()))
        return output[0]

    def _inputs(self, node: ET.Element):
        return self.transform_all_subnodes(node, skip_empty=True, ignored={
            'input-item-list__begin', 'input-item-list'})

    def _input(self, node):
        input_ = self.transform_all_subnodes(node, ignored={'input-item'})
        if len(input_) != 1:
            raise NotImplementedError('exactly one input expected but {} found in:\n{}'.format(
                len(input_), ET.tostring(node).decode().rstrip()))
        return input_[0]

    def _create_file_handle_var(self) -> typed_ast3.Subscript:
        return typed_ast3.Subscript(
            value=typed_ast3.Attribute(value=typed_ast3.Name(id='Fortran', ctx=typed_ast3.Load()),
                                       attr='file_handles', ctx=typed_ast3.Load()),
            slice=typed_ast3.Index(value=None), ctx=typed_ast3.Load())

    def _open(self, node: ET.Element) -> typed_ast3.AnnAssign:
        file_handle = self._create_file_handle_var()
        kwargs = self.transform_one(self.get_one(node, './keyword-arguments'))
        file_handle.slice.value = kwargs.pop(0).value
        filename = None
        mode = ''
        for kwarg in kwargs:
            if kwarg.arg == 'file':
                filename = kwarg.value
            elif kwarg.arg == 'action':
                mode += {
                    'read': 'r',
                    'write': 'w'}[kwarg.value.s]
            elif kwarg.arg == 'form':
                mode += {
                    'formatted': '',
                    'unformatted': 'b'}[kwarg.value.s]
        assert filename is not None, ET.tostring(node).decode().rstrip()
        if not mode:
            mode = 'r'
        assert 0 < len(mode) <= 2, ET.tostring(node).decode().rstrip()
        self.ensure_import('typing', 't')
        return typed_ast3.AnnAssign(
            target=file_handle, value=typed_ast3.Call(
                func=typed_ast3.Name(id='open', ctx=typed_ast3.Load()),
                args=[], keywords=kwargs),
            annotation=typed_ast3.parse('t.IO[bytes]', mode='eval').body, simple=1)

    def _close(self, node: ET.Element) -> typed_ast3.AnnAssign:
        file_handle = self._create_file_handle_var()
        kwargs = self.transform_one(self.get_one(node, './keyword-arguments'))
        file_handle.slice.value = kwargs.pop(0).value
        self.ensure_import('typing', 't')
        return typed_ast3.Call(
            func=typed_ast3.Attribute(value=file_handle, attr='close', ctx=typed_ast3.Load()),
            args=[], keywords=kwargs)

    def _keyword_arguments(self, node: ET.Element):
        kwargs = self.transform_all_subnodes(node, skip_empty=True, ignored={
            'connect-spec-list__begin', 'connect-spec', 'connect-spec-list',
            'close-spec-list__begin', 'close-spec', 'close-spec-list'})
        # TODO: can these really be ignored in all cases?
        return kwargs

    def _keyword_argument(self, node: ET.Element):
        name = node.attrib['argument-name']
        value = self.transform_all_subnodes(node, skip_empty=True, ignored={})
        assert len(value) == 1, value
        return typed_ast3.keyword(arg=name, value=value[0])

    def _transform_mpi_call(
            self, tree: typed_ast3.Call) -> t.Union[typed_ast3.Call, typed_ast3.Assign]:
        assert isinstance(tree, typed_ast3.Call)
        assert tree.func.id.startswith('MPI_')
        assert len(tree.func.id) > 4
        core_name = typed_ast3.Name(id='MPI', ctx=typed_ast3.Load())
        mpi_function_name = tree.func.id[4] + tree.func.id[5:].lower()
        assert len(tree.args) > 0
        # extract last arg -- it's error var
        error_var = tree.args.pop(-1)
        assert isinstance(error_var, typed_ast3.Name), (type(error_var), error_var)
        if mpi_function_name in ('Comm_size', 'Comm_rank', 'Barrier'):
            # extract 1st arg - in some cases it's the MPI scope
            mpi_comm = tree.args.pop(0)
            assert isinstance(mpi_comm, typed_ast3.Name)
            assert mpi_comm.id.startswith('MPI_')
            assert len(mpi_comm.id) > 4
            core_name = typed_ast3.Attribute(
                value=core_name, attr=mpi_comm.id[4:], ctx=typed_ast3.Load())
        tree.func = typed_ast3.Attribute(
            value=core_name, attr=mpi_function_name, ctx=typed_ast3.Load())
        # create assignment of call result to its current 1st var (or 2nd var in some cases)
        if tree.args:
            arg_num = 0
            if mpi_function_name in ('Allreduce',):
                arg_num = 1
            var = tree.args.pop(arg_num)
            assert isinstance(var, typed_ast3.AST)
            tree = typed_ast3.Assign(targets=[var], value=tree, type_comment=None)
        error_var_assignment = typed_ast3.AnnAssign(
            target=error_var, value=None, annotation=typed_ast3.Str(s='MPI error code'), simple=1)
        error_var_assignment = typed_ast3.AnnAssign(
            target=error_var, value=None,
            annotation=typed_ast3.Name(id='int', ctx=typed_ast3.Load()), simple=1)
        error_var_comment = horast_nodes.Comment(value=typed_ast3.Str(' MPI error code'), eol=False)
        return [tree, error_var_assignment, error_var_comment]

    def _assignment(self, node: ET.Element):
        target = self.transform_all_subnodes(self.get_one(node, './target'))
        value = self.transform_all_subnodes(self.get_one(node, './value'))
        if len(target) != 1:
            raise SyntaxError(
                'exactly 1 target expected but {} given {} in:\n{}'
                .format(len(target), target, ET.tostring(node).decode().rstrip()))
        target = target[0]
        assert isinstance(target, typed_ast3.AST)
        if len(value) != 1:
            raise SyntaxError(
                'exactly 1 value expected but {} given {} in:\n{}'
                .format(len(value), value, ET.tostring(node).decode().rstrip()))
        value = value[0]
        assert isinstance(value, typed_ast3.AST)
        return typed_ast3.Assign(targets=[target], value=value, type_comment=None)

    def _pointer_assignment(self, node: ET.Element):
        assignment = self._assignment(node)
        assignment.fortran_metadata = {'is_pointer_assignment': True}
        return assignment

    def _operation(self, node: ET.Element) -> typed_ast3.AST:
        if node.attrib['type'] == 'multiary':
            return self._operation_multiary(node)
        if node.attrib['type'] == 'unary':
            return self._operation_unary(node)
        raise NotImplementedError('not implemented handling of:\n{}'
                                  .format(ET.tostring(node).decode().rstrip()))

    def _operation_multiary(
            self, node: ET.Element) -> t.Union[
                typed_ast3.BinOp, typed_ast3.BoolOp, typed_ast3.Compare]:
        operators_and_operands = self.transform_all_subnodes(node, skip_empty=True, ignored={
            'add-operand', 'mult-operand', 'power-operand', 'and-operand', 'or-operand',
            'parenthesized_expr', 'primary', 'level-2-expr', 'level-3-expr'})
        assert isinstance(operators_and_operands, list), operators_and_operands
        assert len(operators_and_operands) % 2 == 1, operators_and_operands

        operation_type, _ = operators_and_operands[1]
        if operation_type is typed_ast3.BinOp:
            return self._operation_multiary_arithmetic(operators_and_operands)
        if operation_type is typed_ast3.BoolOp:
            return self._operation_multiary_boolean(operators_and_operands)
        if operation_type is typed_ast3.Compare:
            return self._operation_multiary_comparison(operators_and_operands)
        raise NotImplementedError('not implemented handling of:\n{}'
                                  .format(ET.tostring(node).decode().rstrip()))

    def _operation_multiary_arithmetic(
            self, operators_and_operands: t.Sequence[t.Union[typed_ast3.AST, t.Tuple[
                t.Type[typed_ast3.BinOp], t.Type[typed_ast3.AST]]]]) -> typed_ast3.BinOp:
        operators_and_operands = list(reversed(operators_and_operands))
        operators_and_operands += [(None, None)]

        root_operation = None  # type: typed_ast3.BinOp
        operation = None  # type: typed_ast3.BinOp
        root_operation_type = None
        root_operator_type = None
        zippped = zip(operators_and_operands[::2], operators_and_operands[1::2])
        for operand, (operation_type, operator_type) in zippped:
            if root_operation is None:
                root_operation_type = operation_type
                root_operator_type = operator_type
                if root_operation_type is not typed_ast3.BinOp:
                    raise NotImplementedError('root operation initialisation')
                root_operation = typed_ast3.BinOp(
                    left=None, op=root_operator_type(), right=operand)
                operation = root_operation
                continue
            if operation_type is not None:
                assert operation_type is root_operation_type, (operation_type, root_operation_type)
                operation.left = typed_ast3.BinOp(left=None, op=operator_type(), right=operand)
                operation = operation.left
            else:
                operation.left = operand

        return root_operation

    def _operation_multiary_boolean(
            self, operators_and_operands: t.Sequence[t.Union[typed_ast3.AST, t.Tuple[
                t.Type[typed_ast3.BoolOp], t.Type[typed_ast3.AST]]]]) -> typed_ast3.BoolOp:
        operators_and_operands += [(None, None)]

        root_operation = None
        root_operation_type = None
        root_operator_type = None
        zippped = zip(operators_and_operands[::2], operators_and_operands[1::2])
        for operand, (operation_type, operator_type) in zippped:
            if root_operation is None:
                root_operation_type = operation_type
                root_operator_type = operator_type
                if root_operation_type is not typed_ast3.BoolOp:
                    raise NotImplementedError('root operation initialisation')
                root_operation = typed_ast3.BoolOp(
                    op=root_operator_type(), values=[operand])
                continue
            if operation_type is not None:
                assert operation_type is root_operation_type, (operation_type, root_operation_type)
                assert operator_type is root_operator_type, (operator_type, root_operator_type)
            root_operation.values.append(operand)

        return root_operation

    def _operation_multiary_comparison(
            self, operators_and_operands: t.Sequence[t.Union[typed_ast3.AST, t.Tuple[
                t.Type[typed_ast3.Compare], t.Type[typed_ast3.AST]]]]) -> typed_ast3.Compare:
        assert len(operators_and_operands) == 3, operators_and_operands
        left_operand, (operation_type, operator_type), right_operand = operators_and_operands
        assert operation_type is typed_ast3.Compare
        assert not isinstance(right_operand, list), right_operand
        return typed_ast3.Compare(
            left=left_operand, ops=[operator_type()], comparators=[right_operand])

    def _operation_unary(self, node: ET.Element):
        operators_and_operands = self.transform_all_subnodes(node, skip_empty=True, ignored={
            'signed-operand', 'and-operand', 'parenthesized_expr', 'primary'})
        assert isinstance(operators_and_operands, list), operators_and_operands
        assert len(operators_and_operands) == 2, operators_and_operands
        operation_type, operator_type = operators_and_operands[0]
        if operation_type is typed_ast3.BinOp:
            operation_type, operator_type = {
                (typed_ast3.BinOp, typed_ast3.Add): (typed_ast3.UnaryOp, typed_ast3.UAdd),
                (typed_ast3.BinOp, typed_ast3.Sub): (typed_ast3.UnaryOp, typed_ast3.USub)
                }[operation_type, operator_type]
        operand = operators_and_operands[1]
        return operation_type(op=operator_type(), operand=operand)

    def _operand(self, node: ET.Element) -> t.Any:
        operand = self.transform_all_subnodes(node, ignored={
            'add-operand__add-op', 'mult-operand__mult-op', 'and-operand__not-op'})
        if len(operand) != 1:
            _LOG.warning('%s', ET.tostring(node).decode().rstrip())
            # _LOG.error("%s", operand)
            _LOG.error([typed_astunparse.unparse(_).rstrip() for _ in operand])
            raise SyntaxError(
                'expected exactly one operand but got {} in:\n{}'
                .format(len(operand), ET.tostring(node).decode().rstrip()))
        return operand[0]

    def _operator(
            self, node: ET.Element) -> t.Tuple[t.Type[typed_ast3.AST], t.Type[typed_ast3.AST]]:
        return FORTRAN_PYTHON_OPERATORS[node.attrib['operator'].lower()]

    def _array_constructor(self, node: ET.Element) -> typed_ast3.ListComp:
        value_nodes = self.get_all(node, './value')
        values = []
        for value_node in value_nodes:
            value = self.transform_all_subnodes(value_node)
            if not value:
                continue
            assert len(value) == 1
            values.append(value[0])

        if len(values) != 1:
            raise NotImplementedError(
                'not implemented handling of {} in:\n{}'
                .format(values, ET.tostring(node).decode().rstrip()))

        header = self.transform_all_subnodes(self.get_one(node, './header'),
                                             ignored={'ac-implied-do-control'})
        assert len(header) == 1
        comp_target, comp_iter = header[0]
        generator = typed_ast3.comprehension(
            target=comp_target, iter=comp_iter, ifs=[], is_async=0)
        return typed_ast3.ListComp(elt=values[0], generators=[generator])

    def _array_constructor_values(self, node: ET.Element) -> typed_ast3.List:
        value_nodes = self.get_all(node, './value')
        values = []
        for value_node in value_nodes:
            value = self.transform_all_subnodes(value_node)
            if not value:
                continue
            assert len(value) == 1
            values.append(value[0])

        return typed_ast3.List(elts=values, ctx=typed_ast3.Load())

    def _range(self, node: ET.Element) -> typed_ast3.Slice:
        lower_bound = node.find('./lower-bound')
        upper_bound = node.find('./upper-bound')
        step = node.find('./step')
        if lower_bound is not None:
            args = self.transform_all_subnodes(lower_bound)
            assert len(args) == 1, args
            lower_bound = args[0]
        if upper_bound is not None:
            args = self.transform_all_subnodes(upper_bound)
            assert len(args) == 1, args
            upper_bound = args[0]
        if step is not None:
            args = self.transform_all_subnodes(step)
            assert len(args) == 1, args
            step = args[0]
        return typed_ast3.Slice(lower=lower_bound, upper=upper_bound, step=step)

    def _dimensions(self, node: ET.Element) -> t.List[typed_ast3.AST]:
        return self.transform_all_subnodes(node, ignored={'array-spec'})

    def _dimension(self, node: ET.Element) -> t.Union[typed_ast3.Index, typed_ast3.Slice]:
        dim_type = node.attrib['type']
        if dim_type == 'simple':
            values = self.transform_all_subnodes(node, ignored={'array-spec-element'})
            if len(values) != 1:
                _LOG.error('simple dimension should have exactly one value, but it has %i',
                           len(values))
            return typed_ast3.Index(value=values[0])
        elif dim_type == 'range':
            ranges = self.transform_all_subnodes(node, ignored={'array-spec-element'})
            assert len(ranges) == 1, ranges
            return ranges[0]
        elif dim_type == 'assumed-shape':
            return typed_ast3.Slice(lower=None, upper=None, step=None)
        elif dim_type == 'upper-bound-assumed-shape':
            args = self.transform_all_subnodes(node, ignored={'array-spec-element'})
            assert len(args) == 1, args
            lower_bound = args[0]
            return typed_ast3.Slice(lower=lower_bound, upper=None, step=None)
        elif dim_type == 'assumed-size':
            _LOG.warning('generating invalid Python')
            return typed_ast3.Index(value=typed_ast3.Ellipsis())
        else:
            raise NotImplementedError(
                'dimension type "{}" not supported in:\n{}'
                .format(dim_type, ET.tostring(node).decode().rstrip()))

    def _type(self, node: ET.Element) -> type:
        name = node.attrib['name'].lower()
        length = self.transform_one(self.get_one(node, './length')) \
            if node.attrib['hasLength'] == 'true' else None
        kind = self.transform_one(self.get_one(node, './kind')) \
            if node.attrib['hasKind'] == 'true' else None
        if length is not None and kind is not None:
            raise SyntaxError(
                'only one of "length" and "kind" can be provided, but both were given'
                ' ("{}" and "{}" respectively) in:\n{}'
                .format(length, kind, ET.tostring(node).decode().rstrip()))
        if name == 'character':
            if length is not None:
                if isinstance(length, typed_ast3.Num):
                    length = length.n
                _LOG.info(
                    'ignoring string length "%i" in:\n%s',
                    length, ET.tostring(node).decode().rstrip())
            return typed_ast3.parse(FORTRAN_PYTHON_TYPE_PAIRS[name, t.Any], mode='eval').body
        elif length is not None:
            self.ensure_import('numpy', 'np')
            return typed_ast3.parse(FORTRAN_PYTHON_TYPE_PAIRS[name, length], mode='eval').body
        elif kind is not None:
            self.ensure_import('numpy', 'np')
            if isinstance(kind, typed_ast3.Num):
                kind = kind.n
            if not isinstance(kind, int):
                # _LOG.warning('%s', ET.tostring(node).decode().rstrip())
                # raise NotImplementedError('non-literal kinds are not supported')
                python_type = typed_ast3.parse(
                    FORTRAN_PYTHON_TYPE_PAIRS[name, None], mode='eval').body
                self.ensure_import('static_typing', 'st')
                static_type = typed_ast3.Attribute(
                    value=typed_ast3.Name(id='st', ctx=typed_ast3.Load()),
                    attr=python_type, ctx=typed_ast3.Load())
                return typed_ast3.Subscript(
                    value=static_type, slice=typed_ast3.Index(value=kind), ctx=typed_ast3.Load())
                # typed_ast3.parse({
                #    'integer': 'st.int[0]'.format(kind),
                #    'real': lambda kind: 'st.float[0]'.format(kind)}[name](kind), mode='eval')
                # custom_kind_type.
                # return custom_kind_type
            return typed_ast3.parse(FORTRAN_PYTHON_TYPE_PAIRS[name, kind], mode='eval').body
        else:
            if node.attrib['type'] == 'derived':
                return typed_ast3.Call(func=typed_ast3.Name(id='type', ctx=typed_ast3.Load()),
                                       args=[typed_ast3.Name(id=name, ctx=typed_ast3.Load())],
                                       keywords=[])
            assert node.attrib['type'] == 'intrinsic'
            return typed_ast3.parse(FORTRAN_PYTHON_TYPE_PAIRS[name, None], mode='eval').body
        raise NotImplementedError(
            'not implemented handling of:\n{}'.format(ET.tostring(node).decode().rstrip()))

    def _length(self, node):
        values = self.transform_all_subnodes(node, ignored={'char-length'})
        if len(values) == 1:
            return values[0]
        raise NotImplementedError(
            'not implemented handling of:\n{}'.format(ET.tostring(node).decode().rstrip()))

    def _kind(self, node):
        values = self.transform_all_subnodes(node, ignored={'kind-selector'})
        if len(values) == 1:
            return values[0]
        if 'value' in node.attrib:
            return int(node.attrib['value'])
        raise NotImplementedError(
            'not implemented handling of:\n{}'.format(ET.tostring(node).decode().rstrip()))

    def _variable(self, node: ET.Element) -> t.Tuple[typed_ast3.Name, t.Any]:
        value_node = node.find('./initial-value')
        value = None
        if value_node is not None:
            values = self.transform_all_subnodes(value_node, ignored={'initialization'})
            assert len(values) == 1, values
            value = values[0]
        variable = typed_ast3.Name(id=node.attrib['name'], ctx=typed_ast3.Load())
        metadata = {}
        dimensions_node = node.find('./dimensions')
        if dimensions_node is not None:
            metadata['dimensions'] = self.transform_one(dimensions_node)
        if metadata:
            variable.fortran_metadata = metadata
        return variable, value

    def _names(self, node: ET.Element) -> typed_ast3.arguments:
        arguments = self._arguments(node)
        for i, name in enumerate(arguments.args):
            assert isinstance(name, typed_ast3.Name), type(name)
            arguments.args[i] = typed_ast3.arg(arg=name.id, annotation=None)
        return arguments

    def _intrinsic_identity(self, call):
        return call

    def _intrinsic_getenv(self, call):
        assert isinstance(call, typed_ast3.Call), type(call)
        assert len(call.args) + len(call.keywords) == 2, (call.args, call.keywords)
        self.ensure_import('os')
        args_and_keywords = call.args + call.keywords
        target = args_and_keywords[1]
        if isinstance(target, typed_ast3.keyword):
            target = target.value
        return typed_ast3.Assign(
            targets=[target],
            value=typed_ast3.Subscript(
                value=typed_ast3.Attribute(value=typed_ast3.Name(id='os', ctx=typed_ast3.Load()),
                                           attr='environ', ctx=typed_ast3.Load()),
                slice=typed_ast3.Index(value=args_and_keywords[0]), ctx=typed_ast3.Load()),
            type_comment=None)

    def _intrinsic_trim(self, call):
        return typed_ast3.Call(
            func=typed_ast3.Attribute(value=call.args[0], attr='rstrip', ctx=typed_ast3.Load()),
            args=call.args[1:], keywords=[])

    def _intrinsic_count(self, call):
        assert isinstance(call, typed_ast3.Call), type(call)
        assert len(call.args) == 1, call.args
        return typed_ast3.Call(
            func=typed_ast3.Attribute(value=call.args[0], attr='sum', ctx=typed_ast3.Load()),
            args=[], keywords=[])

    def _intrinsic_converter_rename(self, call, name: str):
        assert isinstance(call.func, typed_ast3.Name)
        call.func.id = name
        return call

    def _intrinsic_converter_not_implemented(self, call):
        raise NotImplementedError(
            "cannot convert intrinsic call from raw AST:\n{}"
            .format(typed_astunparse.unparse(call)))

    def _intrinsic_numpy_call(self, call, members=None):
        if not members:
            members = (call.func.id,)
        func = typed_ast3.Name(id='np', ctx=typed_ast3.Load())
        for member in members:
            func = typed_ast3.Attribute(value=func, attr=member, ctx=typed_ast3.Load())
        return typed_ast3.Call(func=func, args=call.args, keywords=call.keywords)

    _convgen_specials = {
        'getenv': _intrinsic_getenv,
        'trim': _intrinsic_trim,
        'count': _intrinsic_count}

    @classmethod
    def _convgen(cls, case, value):
        if value is None:
            return cls._intrinsic_converter_not_implemented
        if case in INTRINSICS_SPECIAL_CASES:
            return cls._convgen_specials[case]
        if case == value:
            return cls._intrinsic_identity
        if isinstance(value, str):
            return functools.partial(cls._intrinsic_converter_rename, name=value)
        assert isinstance(value, tuple), type(value)
        assert len(value) >= 2, value
        package, *members = value
        if package == 'numpy':
            if len(value) == 1 and value[0] == function:
                return cls._intrinsic_numpy_call
            return functools.partial(cls._intrinsic_numpy_call, members=members)
        raise NotImplementedError((case, value))

    _intrinsics_converters = {}

    def _name(self, node: ET.Element) -> typed_ast3.AST:
        name_str = node.attrib['id']
        name = typed_ast3.Name(id=name_str, ctx=typed_ast3.Load())
        name_str = name_str.lower()
        name_type = node.attrib['type'] if 'type' in node.attrib else None
        is_intrinsic = name_str in self._intrinsics_converters

        subscripts_node = node.find('./subscripts')
        try:
            args = self._subscripts(subscripts_node, postprocess=False) if subscripts_node else []
            args, keywords = separate_args_and_keywords(args)
            call = typed_ast3.Call(func=name, args=args, keywords=keywords)
            if is_intrinsic:
                if subscripts_node is None:
                    _LOG.warning('found intrinsic name "%s" without any subscripts', name_str)
                else:
                    name_type = 'function'
                    call = self._intrinsics_converters[name_str](self, call)
        except SyntaxError:
            _LOG.info('transforming name to call failed as below (continuing despite that)',
                      exc_info=True)

        slice_ = self._subscripts(subscripts_node) if subscripts_node else None
        subscript = typed_ast3.Subscript(value=name, slice=slice_, ctx=typed_ast3.Load())

        if name_type in ('procedure', 'function'):
            return call
        elif not subscripts_node:
            return name
        elif name_type in ('variable',):
            return subscript
        elif not slice_:
            return call
        elif name_type in ('ambiguous',):
            return subscript
        elif name_type is not None:
            raise NotImplementedError('unrecognized name type "{}" in:\n{}'
                                      .format(name_type, ET.tostring(node).decode().rstrip()))
        elif name_type is None:
            raise NotImplementedError('no name type in:\n{}'
                                      .format(ET.tostring(node).decode().rstrip()))
        raise NotImplementedError('not implemented handling of:\n{}'
                                  .format(ET.tostring(node).decode().rstrip()))

    def _subscripts(self, node: ET.Element, postprocess: bool = True) -> t.Union[
            typed_ast3.Index, typed_ast3.Slice, typed_ast3.ExtSlice]:
        subscripts = self.transform_all_subnodes(node, ignored={
            'section-subscript-list__begin', 'section-subscript-list'})
        assert len(subscripts) == int(node.attrib['count'])
        if not postprocess:
            return subscripts
        if any(isinstance(_, typed_ast3.Slice) for _ in subscripts):
            if len(subscripts) == 1:
                return subscripts[0]
            return typed_ast3.ExtSlice(dims=[
                (_ if isinstance(_, (typed_ast3.Index, typed_ast3.Slice))
                 else typed_ast3.Index(value=_)) for _ in subscripts])
        assert all(not isinstance(_, (typed_ast3.Index, typed_ast3.Slice, typed_ast3.ExtSlice))
                   for _ in subscripts), subscripts
        if len(subscripts) == 1:
            return typed_ast3.Index(value=subscripts[0])
        return typed_ast3.Index(value=typed_ast3.Tuple(elts=subscripts, ctx=typed_ast3.Load()))

    def _subscript(self, node: ET.Element) -> t.Union[
            typed_ast3.Index, typed_ast3.Slice, typed_ast3.ExtSlice]:
        subscripts = self.transform_all_subnodes(node, ignored={'section-subscript'})
        if not subscripts:
            assert node.attrib['type'] == 'empty'
            return typed_ast3.Slice(lower=None, upper=None, step=None)
        if len(subscripts) != 1:
            self.no_transform(node)
        assert node.attrib['type'] in ('simple', 'range')
        return subscripts[0]

    def _literal(self, node: ET.Element) -> t.Union[typed_ast3.Num, typed_ast3.Str]:
        literal_type = node.attrib['type']
        if literal_type == 'bool':
            return typed_ast3.NameConstant(value={
                'false': False,
                'true': True}[node.attrib['value']])
        if literal_type == 'int':
            return typed_ast3.Num(n=int(node.attrib['value']))
        if literal_type == 'real':
            value = node.attrib['value']
            if 'D' in value:
                value = value.replace('D', 'E', 1)
            return typed_ast3.Num(n=float(value))
        if literal_type == 'char':
            assert len(node.attrib['value']) >= 2
            begin = node.attrib['value'][0]
            end = node.attrib['value'][-1]
            assert begin == end
            return typed_ast3.Str(s=node.attrib['value'][1:-1])
        _LOG.warning('%s', ET.tostring(node).decode().rstrip())
        raise NotImplementedError('literal type "{}" not supported'.format(literal_type))


FortranAstGeneralizer._intrinsics_converters = {
    case: FortranAstGeneralizer._convgen(case, value)
    for case, value in INTRINSICS_FORTRAN_TO_PYTHON.items()}
