"""Transformer of Fortran AST into Python AST."""

import collections.abc
import functools
import itertools
import logging
import typing as t
import xml.etree.ElementTree as ET

import horast.nodes as horast_nodes
import typed_ast.ast3 as typed_ast3
import typed_astunparse

from ..general import Language, AstGeneralizer

_LOG = logging.getLogger(__name__)


def flatten_sequence(sequence: t.MutableSequence[t.Any]) -> None:
    assert isinstance(sequence, collections.abc.MutableSequence)
    for i, elem in enumerate(sequence):
        if isinstance(elem, collections.abc.Sequence):
            for value in reversed(elem):
                sequence.insert(i, value)
            del sequence[i + len(elem)]


FORTRAN_PYTHON_TYPE_PAIRS = {
    ('logical', None): 'bool',
    ('integer', None): 'int',
    ('real', None): 'float',
    ('character', t.Any): 'str',
    ('integer', 1): 'np.int8',
    ('integer', 2): 'np.int16',
    ('integer', 4): 'np.int32',
    ('integer', 8): 'np.int64',
    ('real', 2): 'np.float16',
    ('real', 4): 'np.float32',
    ('real', 8): 'np.float64'}

PYTHON_TYPE_ALIASES = {
    'bool': ('np.bool_',),
    'int': ('np.int_', 'np.intc', 'np.intp'),
    'np.float32': ('np.single',),
    'np.float64': ('np.double', 'np.float_',)}

FORTRAN_PYTHON_FORMAT_SPEC = {
    'A': str,
    'I': int}


class FortranAstGeneralizer(AstGeneralizer):

    """Transform Fortran AST in XML format into typed Python AST.

    The Fortran AST in XML format is provided by XML output generator for Open Fortran Parser.

    Typed Python AST is provided by typed-ast package.
    """

    def __init__(self, split_declarations: bool = True):
        super().__init__(Language.find('Fortran 2008'))
        self._split_declarations = split_declarations

        self._now_parsing_file = False
        self._top_level_imports = dict()
        self._transforms = [f for f in dir(self) if not f.startswith('__')]

    def generalize(self, root_node: ET.Element) -> typed_ast3.AST:
        file_node = root_node[0]
        return self.transform(file_node)

    def _ensure_top_level_import(self, canonical_name: str, alias: t.Optional[str] = None):
        if (canonical_name, alias) not in self._top_level_imports:
            if canonical_name in ('mpif.h', '?'):  # TODO: other ways to include MPI?
                self._ensure_mpi_import(canonical_name, alias)
            else:
                self._top_level_imports[canonical_name, alias] = [typed_ast3.Import(
                    names=[typed_ast3.alias(name=canonical_name, asname=alias)])]

    def _get_node(self, node: ET.Element, xpath: str) -> ET.Element:
        found = node.find(xpath)
        if found is None:
            raise SyntaxError('no "{}" found in "{}":\n{}'
                              .format(xpath, node.tag, ET.tostring(node).decode().rstrip()))
        return found

    def _ensure_mpi_import(self, canonical_name, alias):
        # if ('mpi4py', None) not in self._top_level_imports:
        self._top_level_imports[canonical_name, alias] = [
            typed_ast3.ImportFrom(
                module='mpi4py', names=[typed_ast3.alias(name='MPI', asname=None)], level=0),
            # typed_ast3.parse('mpi4py.config = no_auto_init', mode='eval') # TODO: may be needed
            ]

    def transform(self, node: ET.Element, warn: bool = True):
        transform_name = '_{}'.format(node.tag.replace('-', '_'))
        if transform_name not in self._transforms:
            if warn:
                _LOG.warning('no transformer available for node "%s"', node.tag)
                _LOG.debug('%s', ET.tostring(node).decode().rstrip())
            raise NotImplementedError(
                'no transformer available for node "{}":\n{}'.format(
                    node.tag, ET.tostring(node).decode().rstrip()))
        _transform = getattr(self, transform_name)
        return _transform(node)

    def transform_all_subnodes(
            self, node: ET.Element, warn: bool = True, skip_empty: bool = False,
            ignored: t.Set[str] = None):
        assert node is not None
        transformed = []
        for subnode in node:
            if skip_empty and not subnode.attrib and len(subnode) == 0:
                continue
            transform_name = '_{}'.format(subnode.tag.replace('-', '_'))
            if transform_name not in self._transforms:
                if ignored and subnode.tag in ignored:
                    continue
                if warn:
                    _LOG.warning(
                        'no transformer available for node "%s", a subnode of "%s"',
                        subnode.tag, node.tag)
                    _LOG.debug('%s', ET.tostring(subnode).decode().rstrip())
                    continue
                raise NotImplementedError(
                    'no transformer available for node "{}", a subnode of "{}":\n{}'.format(
                        subnode.tag, node.tag, ET.tostring(subnode).decode().rstrip()))
            if ignored and subnode.tag in ignored:
                _LOG.warning('ignoring existing transformer for %s', subnode.tag)
                continue
            _transform = getattr(self, transform_name)
            transformed.append(_transform(subnode))
        return transformed

    def _file(self, node: ET.Element) -> t.Union[typed_ast3.Module, typed_ast3.Expr]:
        if not self._now_parsing_file:
            self._now_parsing_file = True
            body = self.transform_all_subnodes(
                node, warn=False, ignored={'start-of-file', 'end-of-file'})
            self._now_parsing_file = False
            import_statements = list(itertools.chain(
                *[statements for _, statements in self._top_level_imports.items()]))
            body = import_statements + body
        else:
            return typed_ast3.Expr(value=typed_ast3.Call(
                func=typed_ast3.Name(id='print'),
                args=[typed_ast3.Str(s='file'), typed_ast3.Str(s=node.attrib['path'])],
                keywords=[]))
        return typed_ast3.Module(body=body, type_ignores=[])

    def _comment(self, node: ET.Element) -> horast_nodes.Comment:
        comment = node.attrib['text']
        if len(comment) == 0 or comment[0] not in ('!', 'c', 'C'):
            raise SyntaxError('comment token {} has unexpected prefix'.format(repr(comment)))
        comment = comment[1:]
        return horast_nodes.Comment(value=typed_ast3.Str(s=comment), eol=False)

    def _directive(self, node) -> horast_nodes.Comment:
        directive = node.attrib['text']
        if len(directive) == 0 or directive[0] not in ('#'):
            raise SyntaxError('directive token {} has unexpected prefix'.format(repr(comment)))
        directive = directive[1:]
        directive_ = horast_nodes.Comment(value=typed_ast3.Str(s=directive), eol=False)
        directive_.fortran_metadata = {'is_directive': True}
        return directive_

    def _module(self, node: ET.Element):
        _ = typed_ast3.parse('''if __name__ == '__main__':\n    pass''')
        body = self.transform_all_subnodes(node.find('./body'))
        conditional = _.body[0]
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
        # raise NotImplementedError('not implemented handling of:\n{}'.format(ET.tostring(node).decode().rstrip()))

    def _function(self, node: ET.Element):
        arguments = self.transform(node.find('./header/names'))
        body = self.transform_all_subnodes(node.find('./body'))
        return typed_ast3.FunctionDef(
            name=node.attrib['name'], args=arguments, body=body, decorator_list=[],
            returns=typed_ast3.NameConstant(None))

    def _subroutine(self, node: ET.Element) -> typed_ast3.FunctionDef:
        header_node = node.find('./header')
        if header_node is None:
            raise SyntaxError(
                'no "header" found in "subroutine":\n{}'
                .format(ET.tostring(node).decode().rstrip()))
        arguments_node = node.find('./header/arguments')
        if arguments_node is None:
            arguments = []
        else:
            arguments = self.transform(arguments_node)
        body = self.transform_all_subnodes(node.find('./body'))
        return typed_ast3.FunctionDef(
            name=node.attrib['name'], args=arguments, body=body, decorator_list=[],
            returns=typed_ast3.NameConstant(None))

    def _arguments(self, node: ET.Element) -> typed_ast3.arguments:
        return typed_ast3.arguments(
            args=self.transform_all_subnodes(
                node, warn=False, ignored={
                    'dummy-arg-list__begin', 'dummy-arg-list'} | {'generic-name-list__begin', 'generic-name-list'}),
            vararg=None, kwonlyargs=[], kwarg=None, defaults=[], kw_defaults=[])

    def _argument(self, node: ET.Element) -> typed_ast3.arg:
        if 'name' not in node.attrib:
            raise SyntaxError(
                '"name" attribute not present in:\n{}'.format(ET.tostring(node).decode().rstrip()))
        values = self.transform_all_subnodes(
            node, warn=False, skip_empty=False,
            ignored={'actual-arg', 'actual-arg-spec', 'dummy-arg'})
        if values:
            assert len(values) == 1
            return typed_ast3.keyword(arg=node.attrib['name'], value=values[0])
        return typed_ast3.arg(arg=node.attrib['name'], annotation=None)

    def _return(self, node: ET.Element) -> typed_ast3.Return:
        has_value = node.attrib['hasValue'] == 'true'
        if not has_value:
            return typed_ast3.Return(value=None)
        raise NotImplementedError(
            'not implemented handling of:\n{}'.format(ET.tostring(node).decode().rstrip()))

    def _stop(self, node: ET.Element) -> typed_ast3.Call:
        _LOG.warning('ignoring exit code in """%s"""', ET.tostring(node).decode().rstrip())
        return typed_ast3.Call(func=typed_ast3.Name(id='exit'), args=[], keywords=[])

    def _program(self, node: ET.Element) -> typed_ast3.AST:
        module = typed_ast3.parse('''if __name__ == '__main__':\n    pass''')
        body = self.transform_all_subnodes(node.find('./body'))
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
        declarations = self.transform_all_subnodes(
            node, warn=False, skip_empty=True,
            ignored={'declaration-construct', 'specification-part'})
        return declarations

    def _declaration(self, node: ET.Element) -> typed_ast3.AnnAssign:
        #if 'type' not in node.attrib:
        #    # return []  # TODO: TMP
        #    raise SyntaxError(
        #        '"type" attribute not present in:\n{}'.format(ET.tostring(node).decode().rstrip()))
        declaration_type = node.attrib.get('type', None)
        if declaration_type is None:
            pass
        elif declaration_type == 'implicit':
            # TODO: generate comment here maybe?
            if node.attrib['subtype'].lower() == 'none':
                annotation = typed_ast3.NameConstant(value=None)
            else:
                annotation = typed_ast3.Str(s=node.attrib['subtype'])
            return typed_ast3.AnnAssign(
                target=typed_ast3.Name(id='implicit'), annotation=annotation, value=None,
                simple=True)
        elif declaration_type == 'variable':
            return self._declaration_variable(node)
        elif declaration_type == 'parameter':
            return self._declaration_parameter(node)
        elif declaration_type == 'include':
            return self._declaration_include(node)
        elif declaration_type in ('data', 'external'):
            return typed_ast3.Expr(value=typed_ast3.Call(
                func=typed_ast3.Name(id='print'),
                args=[typed_ast3.Str(s='declaration'), typed_ast3.Str(s=node.attrib['type'])],
                keywords=[]))
        details = self.transform_all_subnodes(node, warn=False, ignored={})
        flatten_sequence(details)
        return details
        # raise NotImplementedError(
        #    'not implemented handling of:\n{}'.format(ET.tostring(node).decode().rstrip()))

    def _declaration_variable(
            self, node: ET.Element) -> t.Union[
                typed_ast3.Assign, typed_ast3.AnnAssign, t.List[typed_ast3.Assign],
                t.List[typed_ast3.AnnAssign]]:
        variables_node = node.find('./variables')
        if variables_node is None:
            _LOG.error('%s', ET.tostring(node).decode().rstrip())
            raise SyntaxError('"variables" node not present')
        variables = self.transform_all_subnodes(
            variables_node, warn=False, skip_empty=True,
            ignored={'entity-decl-list__begin', 'entity-decl-list'})
        if not variables:
            _LOG.error('%s', ET.tostring(node).decode().rstrip())
            raise SyntaxError('at least one variable expected in variables list')
        if len(variables) == 1:
            target, value = variables[0]
        else:
            target = typed_ast3.Tuple(elts=[var for var, _ in variables])
            value = [val for _, val in variables]

        type_node = node.find('./type')
        if type_node is None:
            raise SyntaxError('"type" node not present in\n{}', ET.tostring(node).decode().rstrip())
        annotation = self.transform(type_node)

        dimensions_node = node.find('./dimensions')
        dimensions = None
        if any(['dimensions' in getattr(var, 'fortran_metadata', {}) for var, _ in variables]):
            if dimensions_node is not None:
                raise SyntaxError('many dimensions definitions for single variable')
            if len(variables) > 1:
                raise NotImplementedError('conflicting dimensions information')
            dimensions_node = 'found in variable'
            dimensions = variables[0][0].fortran_metadata['dimensions']
        if dimensions_node is not None:
            if dimensions is None:
                dimensions = self.transform(dimensions_node)
            assert len(dimensions) >= 1
            data_type = annotation
            self._ensure_top_level_import('static_typing', 'st')
            annotation = typed_ast3.Subscript(
                value=typed_ast3.Attribute(
                    value=typed_ast3.Name(id='st', ctx=typed_ast3.Load()),
                    attr='ndarray', ctx=typed_ast3.Load()),
                # slice=typed_ast3.ExtSlice(dims=[typed_ast3.Num(n=len(dimensions)), data_type]),
                slice=typed_ast3.Index(value=typed_ast3.Tuple(
                    elts=[typed_ast3.Num(n=len(dimensions)), data_type,
                          typed_ast3.Tuple(elts=[_ for _ in dimensions])])),
                ctx=typed_ast3.Load())
            if len(variables) > 1:
                if all([_ is None for _ in value]):
                    self._ensure_top_level_import('numpy', 'np')
                    for i, (var, _) in enumerate(variables):
                        # val = typed_ast3.Call(
                        #    func=typed_ast3.Attribute(value=typed_ast3.Name(id='np'),
                        #                              attr='zeros', ctx=typed_ast3.Load()),
                        #    args=[typed_ast3.Tuple(elts=dimensions)],
                        #    keywords=[typed_ast3.keyword(arg='dtype', value=data_type)])
                        # variables[i] = (var, val)
                        variables[i] = (var, None)
                    # value = [ for _ in variables]
                    value = [val for _, val in variables]
                else:
                    raise NotImplementedError(
                        'not implemented handling of many initial values {}:\n{}'.format(
                            [typed_ast3.dump(_) for _ in value],
                            ET.tostring(node).decode().rstrip()))
            elif len(variables) == 1:
                if value is not None:
                    value = typed_ast3.Call(
                        func=typed_ast3.Attribute(
                            value=typed_ast3.Name(id='np'), attr='array', ctx=typed_ast3.Load()),
                        args=[value],
                        keywords=[typed_ast3.keyword(arg='dtype', value=data_type)])
                    # raise NotImplementedError(
                    #    'not implemented handling of initial value {}:\n{}'
                    #    .format(typed_ast3.dump(value), ET.tostring(node).decode().rstrip()))
                else:
                    pass
            else:
                raise ValueError(len(variables))

        metadata = {}
        intent_node = node.find('./intent')
        if intent_node is not None:
            metadata['intent'] = intent_node.attrib['type']

        pointer_node = node.find('./pointer')
        if pointer_node is not None:
            metadata['is_pointer'] = True

        if metadata:
            metadata_node = horast_nodes.Comment(
                value=typed_ast3.Str(s=' Fortran metadata: {}'.format(repr(metadata))), eol=False)

        if len(variables) == 1:
            assignments = [typed_ast3.AnnAssign(
                target=target, annotation=annotation, value=value, simple=True)]
        else:
            assert len(variables) == len(value)
            if not self._split_declarations:
                value = typed_ast3.Tuple(
                    elts=[typed_ast3.NameConstant(value=None) if v is None else v for v in value])
                type_comment = typed_astunparse.unparse(
                    typed_ast3.Tuple(elts=[annotation for _ in range(len(variables))])).strip()
                assignments = [typed_ast3.Assign(
                    argets=[target], value=value, type_comment=type_comment)]
            assignments = [
                typed_ast3.AnnAssign(target=var, annotation=annotation, value=val, simple=True)
                for var, val in variables]
        if not metadata:
            if len(assignments) == 1:
                return assignments[0]
        else:
            for assignment in assignments:
                assignment.fortran_metadata = metadata
            if self._split_declarations:
                new_assignments = []
                for assignment in assignments:
                    new_assignments.append(assignment)
                    new_assignments.append(metadata_node)
                assignments = new_assignments
            else:
                assignments.append(metadata_node)
        return assignments

    def _declaration_parameter(self, node: ET.Element):
        constants_node = node.find('./constants')
        constants = self.transform_all_subnodes(
            constants_node, warn=False, skip_empty=True,
            ignored={'named-constant-def-list__begin', 'named-constant-def-list'})
        assignments = []
        for constant, value in constants:
            assignment = typed_ast3.Assign(targets=[constant], value=value, type_comment=None)
            assignment.fortran_metadata = {'is_constant': True}
            assignments.append(assignment)
        return assignments

    def _constant(self, node: ET.Element) -> t.Tuple[typed_ast3.Name, t.Any]:
        values = self.transform_all_subnodes(node, warn=False, ignored={'named-constant-def'})
        assert len(values) == 1
        value = values[0]
        name = typed_ast3.Name(id=node.attrib['name'], ctx=typed_ast3.Load())
        return name, value

    def _declaration_include(self, node: ET.Element) -> typed_ast3.Import:
        file_node = node.find('./file')
        path_attrib = file_node.attrib['path']
        self._ensure_top_level_import(path_attrib)
        return typed_ast3.Import(names=[typed_ast3.alias(name=path_attrib, asname=None)])

    def _format(self, node: ET.Element) -> t.Union[typed_ast3.AnnAssign, typed_ast3.JoinedStr]:
        format_items_node = node.find('./format-items')
        value = self.transform(format_items_node, warn=False)
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
        items = self.transform_all_subnodes(
            node, warn=False, ignored={'format-item-list__begin', 'format-item-list'})
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
        elif node.attrib['type'] == 'forall':
            return self._loop_forall(node)
        else:
            raise NotImplementedError(
                'not implemented handling of:\n{}'.format(ET.tostring(node).decode().rstrip()))

    def _loop_do(self, node: ET.Element) -> typed_ast3.For:
        index_variable = node.find('./header/index-variable')
        body_node = node.find('./body')
        if index_variable is None or body_node is None:
            raise SyntaxError('at least one of required sub nodes is not present in:\n{}'
                              .format(ET.tostring(node).decode().rstrip()))
        target, iter_ = self._index_variable(index_variable)
        body = self.transform_all_subnodes(body_node, warn=False, ignored={'block'})
        return typed_ast3.For(target=target, iter=iter_, body=body, orelse=[])

    def _loop_implied_do(self, node: ET.Element) -> typed_ast3.ListComp:
        index_variable = node.find('./header/index-variable')
        body_node = node.find('./body')
        if index_variable is None or body_node is None:
            raise SyntaxError('at least one of required sub nodes is not present in:\n{}'
                              .format(ET.tostring(node).decode().rstrip()))
        comp_target, comp_iter = self._index_variable(index_variable)
        expressions = self.transform_all_subnodes(body_node, warn=False, ignored={})
        assert len(expressions) > 0
        elt = expressions[0] if len(expressions) == 1 else typed_ast3.Tuple(elts=expressions)
        generator = typed_ast3.comprehension(
            target=comp_target, iter=comp_iter, ifs=[], is_async=0)
        return typed_ast3.ListComp(elt=elt, generators=[generator])
        # target=target, iter=iter_, body=body, orelse=[])

    def _loop_do_while(self, node: ET.Element) -> typed_ast3.While:
        header_node = node.find('./header')
        header = self.transform_all_subnodes(header_node, warn=False)
        assert len(header) == 1
        condition = header[0]
        body = self.transform_all_subnodes(node.find('./body'), warn=False, ignored={'block'})
        return typed_ast3.While(test=condition, body=body, orelse=[])

    def _loop_forall(self, node: ET.Element) -> typed_ast3.For:
        index_variables = node.find('./header/index-variables')
        outer_loop = None
        inner_loop = None
        for index_variable in index_variables.findall('./index-variable'):
            if not index_variable:
                continue # TODO: this is just a duct tape
            target, iter_ = self._index_variable(index_variable)
            if outer_loop is None:
                outer_loop = typed_ast3.For(target=target, iter=iter_, body=[], orelse=[])
                inner_loop = outer_loop
                continue
            inner_loop.body = [typed_ast3.For(target=target, iter=iter_, body=[], orelse=[])]
            inner_loop = inner_loop.body[0]
        #inner_loop.body = [self.transform(self._get_node(node, './assignmet'))]
        inner_loop.body = self.transform_all_subnodes(self._get_node(node, './body'), warn=False)
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
            args = self.transform_all_subnodes(upper_bound, warn=False)
            assert len(args) == 1, args
            range_args.append(typed_ast3.BinOp(
                left=args[0], op=typed_ast3.Add(), right=typed_ast3.Num(n=1)))
        if step is not None:
            args = self.transform_all_subnodes(step, warn=False)
            assert len(args) == 1, args
            range_args.append(args[0])
        iter_ = typed_ast3.Call(
            func=typed_ast3.Name(id='range', ctx=typed_ast3.Load()),
            args=range_args, keywords=[])
        return target, iter_

    def _cycle(self, node: ET.Element) -> typed_ast3.Continue:
        return typed_ast3.Continue()

    def _exit(self, node: ET.Element) -> typed_ast3.Break:
        return typed_ast3.Break()

    def _if(self, node: ET.Element):
        headers = node.findall('./header')
        bodies = node.findall('./body')
        outermost_if = None
        current_if = None
        for header, body in itertools.zip_longest(headers, bodies):
            if outermost_if is None:
                outermost_if = self._if_if(header, body)
                current_if = outermost_if
                continue
            new_if = self._if_else(body) if header is None \
                else self._if_elif(header, body)
            current_if.orelse.append(new_if)
            current_if = current_if.orelse[-1]
        return outermost_if

    def _if_if(self, header_node: ET.Element, body_node: ET.Element) -> typed_ast3.If:
        header = self.transform_all_subnodes(
            header_node, warn=False, ignored={'executable-construct', 'execution-part-construct'})
        if len(header) != 1:
            _LOG.error('parsed results: %s', [typed_astunparse.unparse(_).rstrip() for _ in header])
            raise NotImplementedError('not implemented handling of:\n{}'
                                      .format(ET.tostring(header_node).decode().rstrip()))
        body = self._if_body(body_node)
        if_ = typed_ast3.If(test=header[0], body=body, orelse=[])
        return if_

    def _if_body(self, body_node: ET.Element) -> typed_ast3.If:
        return self.transform_all_subnodes(body_node, skip_empty=True, ignored={'block'})

    def _if_elif(self, header_node: ET.Element, body_node: ET.Element) -> typed_ast3.If:
        assert header_node.attrib['type'] == 'else-if'
        assert body_node.attrib['type'] == 'else-if'
        return self._if_if(header_node, body_node)

    def _if_else(self, body_node: ET.Element):
        assert body_node.attrib['type'] == 'else'
        return self._if_body(body_node)

    def _expressions(self, node: ET.Element) -> t.List[typed_ast3.AST]:
        return self.transform_all_subnodes(node, warn=False, ignored={
            'allocate-object-list__begin', 'allocate-object-list',
            'allocation-list__begin', 'allocation-list'
            })

    def _expression(self, node) -> typed_ast3.AST:
        expression = self.transform_all_subnodes(node, warn=True, ignored={
            'allocate-object',
            'allocation'})
        if len(expression) != 1:
            raise NotImplementedError('exactly one output expected but {} found in:\n{}'.format(
                len(expression), ET.tostring(node).decode().rstrip()))
        return expression[0]

    def _statement(self, node: ET.Element):
        details = self.transform_all_subnodes(
            node, warn=False, ignored={
                'action-stmt', 'executable-construct', 'execution-part-construct',
                'execution-part'})
        flatten_sequence(details)
        #if len(details) == 0:
        #    args = [
        #        typed_ast3.Str(s=ET.tostring(node).decode().rstrip()),
        #        typed_ast3.Num(n=len(node))]
        #    return [
        #        typed_ast3.Expr(value=typed_ast3.Call(
        #            func=typed_ast3.Name(id='print', ctx=typed_ast3.Load()),
        #            args=args, keywords=[])),
        #        typed_ast3.Pass()]
        return [
            detail if isinstance(detail, (typed_ast3.Expr, typed_ast3.Assign, typed_ast3.AnnAssign))
            else typed_ast3.Expr(value=detail)
            for detail in details]

    def _allocate(self, node: ET.Element) -> t.List[typed_ast3.Assign]:
        expressions_node = node.find('./expressions')
        expressions = self.transform(expressions_node, warn=False)
        assignments = []
        for expression in expressions:
            assert isinstance(expression, typed_ast3.Subscript), type(expression)
            var = expression.value
            if isinstance(expression.slice, typed_ast3.Index):
                sizes = [expression.slice.value]
            elif isinstance(expression.slice, typed_ast3.ExtSlice):
                sizes = expression.slice.dims
            else:
                raise NotImplementedError('unrecognized slice type: "{}"'
                                          .format(type(expression.slice)))
            val = typed_ast3.Call(
                func=typed_ast3.Attribute(
                    value=typed_ast3.Name(id='np'), attr='zeros', ctx=typed_ast3.Load()),
                args=[typed_ast3.Tuple(elts=sizes)],
                keywords=[typed_ast3.keyword(arg='dtype', value=typed_ast3.Attribute(
                    value=typed_ast3.Name(id='t', ctx=typed_ast3.Load()), attr='Any',
                    ctx=typed_ast3.Load()))])
            assignment = typed_ast3.Assign(targets=[var], value=val, type_comment=None)
            assignment.fortran_metadata = {'is_allocation': True}
            assignments.append(assignment)
            assignments.append(horast_nodes.Comment(typed_ast3.Str(
                s=' Fortran metadata: {}'.format(repr(assignment.fortran_metadata))), eol=True))
        return assignments

    '''
    def _allocations(self, node: ET.Element) -> typed_ast3.Assign:
        allocation_nodes = node.findall('./allocation')
        allocations = []
        for allocation_node in allocation_nodes:
            if not allocation_node:
                continue
            allocation = self.transform_all_subnodes(allocation_node, warn=False)
            assert len(allocation) == 1
            allocations.append(allocation[0])
        assert len(allocations) == int(node.attrib['count']), (len(allocations), node.attrib['count'])
        assignments = []
        for allocation in allocations:
            assert isinstance(allocation, typed_ast3.Subscript)
            var = allocation.value
            if isinstance(allocation.slice, typed_ast3.Index):
                sizes = [allocation.slice.value]
            elif isinstance(allocation.slice, typed_ast3.ExtSlice):
                sizes = allocation.slice.dims
            else:
                raise NotImplementedError('unrecognized slice type: "{}"'.format(type(allocation.slice)))
            val = typed_ast3.Call(
                func=typed_ast3.Attribute(
                    value=typed_ast3.Name(id='np'), attr='zeros', ctx=typed_ast3.Load()),
                args=[typed_ast3.Tuple(elts=sizes)], keywords=[typed_ast3.keyword(arg='dtype', value='t.Any')])
            assignments.append(
                typed_ast3.Assign(targets=[var], value=val, type_comment=None))
        return assignments
    '''

    def _deallocate(self, node: ET.Element) -> typed_ast3.Delete:
        expressions_node = node.find('./expressions')
        expressions = self.transform(expressions_node, warn=False)
        targets = []
        for expression in expressions:
            assert isinstance(expression, typed_ast3.Name), type(expression)
            #raise NotImplementedError('not handling:\n{}'.format(typed_astunparse.dump(expression)))
            targets.append(expression)
        return typed_ast3.Delete(targets=targets)

    #def _allocate_objects(self, node: ET.Element) -> typed_ast3.Delete:
    #    pass

    #def _allocate_object(self, node: ET.Element) -> typed_ast3.Delete:
    #    return self._expression(node)

    def _call(self, node: ET.Element) -> t.Union[typed_ast3.Call, typed_ast3.Assign]:
        called = self.transform_all_subnodes(node, warn=False, ignored={'call-stmt'})
        if len(called) != 1:
            raise SyntaxError(
                'call statement must contain a single called object, not {}, like in:\n{}'.format(
                    [typed_astunparse.unparse(_).rstrip() for _ in called],
                    ET.tostring(node).decode().rstrip()))
        call = called[0]
        if not isinstance(call, typed_ast3.Call):
            name_node = node.find('./name')
            is_intrinsic = name_node.attrib['id'] in self._intrinsics_converters if name_node is not None else False
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
            args = self.transform(io_controls_node, warn=False)
        outputs_node = node.find('./outputs')
        if outputs_node is not None:
            written = self.transform(outputs_node, warn=False)
        if len(written) > 1 or len(args) > 1:
            # file
            pass
        else:
            # string
            pass
        args += written
        return typed_ast3.Expr(value=typed_ast3.Call(
            func=typed_ast3.Name(id='write', ctx=typed_ast3.Load()),
            args=args, keywords=[]))

    def _read(self, node: ET.Element):
        file_handle = self._create_file_handle_var()
        io_controls = self.transform(node.find('./io-controls'), warn=False)
        inputs = self.transform(node.find('./inputs'), warn=False)
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
        return [
            typed_ast3.Assign(
                targets=[input_], value=typed_ast3.Call(
                    func=typed_ast3.Attribute(
                        value=file_handle, attr='read', ctx=typed_ast3.Load()),
                    args=[], keywords=[]),
                type_comment=None)
            for input_ in inputs]

    def _print(self, node):
        format_node = node.find('./print-format')
        format_ = None
        #if format_node is not None:
        if format_node.attrib['type'] == 'label':
            format_ = self.transform(format_node, warn=False)
        outputs_node = node.find('./outputs')
        args = []
        if outputs_node is not None:
            args = self.transform(outputs_node, warn=False)
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
        return typed_ast3.Expr(value=typed_ast3.Call(
            func=typed_ast3.Name(id='print', ctx=typed_ast3.Load()),
            args=args, keywords=[]))

    def _print_format(self, node: ET.Element) -> t.Union[None, typed_ast3.Num, typed_ast3.Str]:
        fmt = self.transform_all_subnodes(node, warn=False, ignored={'format'})
        if not fmt:
            return None
        assert len(fmt) == 1, (len(fmt), fmt)
        assert isinstance(fmt[0], (typed_ast3.Num, typed_ast3.Str)), type(fmt[0])
        return fmt[0]

    def _io_controls(self, node: ET.Element):
        return self.transform_all_subnodes(
            node, warn=False, skip_empty=True,
            ignored={'io-control-spec-list__begin', 'io-control-spec-list'})

    def _io_control(self, node) -> typed_ast3.AST:
        io_control = self.transform_all_subnodes(node)
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
        return self.transform_all_subnodes(
            node, warn=False, skip_empty=True,
            ignored={'output-item-list__begin', 'output-item-list'})

    def _output(self, node):
        output = self.transform_all_subnodes(node, warn=False, ignored={'output-item'})
        if len(output) != 1:
            raise NotImplementedError('exactly one output expected but {} found in:\n{}'.format(
                len(output), ET.tostring(node).decode().rstrip()))
        return output[0]

    def _inputs(self, node: ET.Element):
        return self.transform_all_subnodes(
            node, warn=False, skip_empty=True,
            ignored={'input-item-list__begin', 'input-item', 'input-item-list'})

    def _input(self, node):
        input_ = self.transform_all_subnodes(node)
        if len(input_) != 1:
            raise NotImplementedError('exactly one input expected but {} found in:\n{}'.format(
                len(input_), ET.tostring(node).decode().rstrip()))
        return input_[0]

    def _create_file_handle_var(self):
        return typed_ast3.Subscript(
            value=typed_ast3.Attribute(value=typed_ast3.Name(id='Fortran', ctx=typed_ast3.Load()),
                                       attr='file_handles', ctx=typed_ast3.Load()),
            slice=typed_ast3.Index(value=None), ctx=typed_ast3.Load())

    def _open(self, node: ET.Element) -> typed_ast3.AnnAssign:
        file_handle = self._create_file_handle_var()
        kwargs = self.transform(node.find('./keyword-arguments'), warn=False)
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
        self._ensure_top_level_import('typing', 't')
        return typed_ast3.AnnAssign(
            target=file_handle, value=typed_ast3.Call(
                func=typed_ast3.Name(id='open', ctx=typed_ast3.Load()),
                args=[], keywords=kwargs),
            annotation=typed_ast3.parse('t.IO[bytes]', mode='eval').body, simple=1)

    def _close(self, node: ET.Element) -> typed_ast3.AnnAssign:
        file_handle = self._create_file_handle_var()
        kwargs = self.transform(node.find('./keyword-arguments'), warn=False)
        file_handle.slice.value = kwargs.pop(0).value
        self._ensure_top_level_import('typing', 't')
        return typed_ast3.Call(
            func=typed_ast3.Attribute(value=file_handle, attr='close', ctx=typed_ast3.Load()),
            args=[], keywords=kwargs)

    def _keyword_arguments(self, node: ET.Element):
        kwargs = self.transform_all_subnodes(
            node, warn=False, skip_empty=True, ignored={
                'connect-spec-list__begin', 'connect-spec', 'connect-spec-list',
                'close-spec-list__begin', 'close-spec', 'close-spec-list'})
        # TODO: can these really be ignored in all cases?
        return kwargs

    def _keyword_argument(self, node: ET.Element):
        name = node.attrib['argument-name']
        value = self.transform_all_subnodes(node, warn=False, skip_empty=True, ignored={})
        assert len(value) == 1, value
        return typed_ast3.keyword(arg=name, value=value[0])

    def _transform_mpi_call(
            self, tree: typed_ast3.Call) -> t.Union[typed_ast3.Call, typed_ast3.Assign]:
        assert isinstance(tree, typed_ast3.Call)
        assert tree.func.id.startswith('MPI_')
        assert len(tree.func.id) > 4
        core_name = typed_ast3.Name(id='MPI')
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
            tree = typed_ast3.Assign(targets=[var], value=tree, type_comment=None)
        error_var_assignment = typed_ast3.AnnAssign(
            target=error_var, value=None, annotation=typed_ast3.Str(s='MPI error code'), simple=1)
        error_var_assignment = typed_ast3.AnnAssign(
            target=error_var, value=None, annotation=typed_ast3.Name(id='int'), simple=1)
        error_var_comment = horast_nodes.Comment(value=typed_ast3.Str(' MPI error code'), eol=False)
        return [tree, error_var_assignment, error_var_comment]

    def _assignment(self, node: ET.Element):
        target = self.transform_all_subnodes(node.find('./target'))
        value = self.transform_all_subnodes(node.find('./value'))
        if len(target) != 1:
            raise SyntaxError(
                'exactly 1 target expected but {} given {} in:\n{}'
                .format(len(target), target, ET.tostring(node).decode().rstrip()))
        if len(value) != 1:
            raise SyntaxError(
                'exactly 1 value expected but {} given {} in:\n{}'
                .format(len(value), value, ET.tostring(node).decode().rstrip()))
        return typed_ast3.Assign(targets=[target], value=value, type_comment=None)

    def _operation(self, node: ET.Element) -> typed_ast3.AST:
        if node.attrib['type'] == 'multiary':
            return self._operation_multiary(node)
        if node.attrib['type'] == 'unary':
            return self._operation_unary(node)
        raise NotImplementedError(
            f'not implemented handling of:\n{ET.tostring(node).decode().rstrip()}')

    def _operation_multiary(
            self, node: ET.Element) -> t.Union[
                typed_ast3.BinOp, typed_ast3.BoolOp, typed_ast3.Compare]:
        operators_and_operands = self.transform_all_subnodes(
            node, skip_empty=True, ignored={
                'add-operand', 'mult-operand', 'parenthesized_expr',
                # 'add-operand__add-op', 'mult-operand__mult-op',
                'primary', 'level-2-expr', 'level-3-expr'})
        assert isinstance(operators_and_operands, list), operators_and_operands
        assert len(operators_and_operands) % 2 == 1, operators_and_operands

        operation_type, _ = operators_and_operands[1]
        if operation_type is typed_ast3.BinOp:
            return self._operation_multiary_arithmetic(operators_and_operands)
        if operation_type is typed_ast3.BoolOp:
            return self._operation_multiary_boolean(operators_and_operands)
        if operation_type is typed_ast3.Compare:
            return self._operation_multiary_comparison(operators_and_operands)
        raise NotImplementedError('not implemented handling of:\n{}'.format(ET.tostring(node).decode().rstrip()))

    def _operation_multiary_arithmetic(
            self, operators_and_operands: t.Sequence[t.Union[typed_ast3.AST, t.Tuple[
                t.Type[typed_ast3.BinOp], t.Type[typed_ast3.AST]]]]) -> typed_ast3.BinOp:
        operators_and_operands = list(reversed(operators_and_operands))
        operators_and_operands += [(None, None)]

        root_operation = None
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
        return typed_ast3.Compare(
            left=left_operand, ops=[operator_type()], comparators=[right_operand])

    def _operation_unary(self, node: ET.Element):
        operators_and_operands = self.transform_all_subnodes(
            node, skip_empty=True) #, ignored={
            #    'add-operand__add-op', 'add-operand', 'mult-operand__mult-op', 'mult-operand',
            #    'primary'})
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
            'add-operand__add-op', 'mult-operand__mult-op',  # 'power-operand'
            })
        if len(operand) != 1:
            _LOG.warning('%s', ET.tostring(node).decode().rstrip())
            #_LOG.error("%s", operand)
            _LOG.error([typed_astunparse.unparse(_).rstrip() for _ in operand])
            raise SyntaxError(
                'expected exactly one operand but got {} in:\n{}'
                .format(len(operand), ET.tostring(node).decode().rstrip()))
        return operand[0]

    def _operator(
            self, node: ET.Element) -> t.Tuple[t.Type[typed_ast3.AST], t.Type[typed_ast3.AST]]:
        return {
            # binary
            '+': (typed_ast3.BinOp, typed_ast3.Add),
            '-': (typed_ast3.BinOp, typed_ast3.Sub),
            '*': (typed_ast3.BinOp, typed_ast3.Mult),
            # missing: MatMult
            '/': (typed_ast3.BinOp, typed_ast3.Div),
            '%': (typed_ast3.BinOp, typed_ast3.Mod),
            '**': (typed_ast3.BinOp, typed_ast3.Pow),
            '//': (typed_ast3.BinOp, typed_ast3.Add), # concatenation operator, only in Fortran
            # LShift
            # RShift
            # BitOr
            # BitXor
            # BitAnd
            # missing: FloorDiv
            '.eq.': (typed_ast3.Compare, typed_ast3.Eq),
            '==': (typed_ast3.Compare, typed_ast3.Eq),
            '.ne.': (typed_ast3.Compare, typed_ast3.NotEq),
            '/=': (typed_ast3.Compare, typed_ast3.NotEq),
            '.lt.': (typed_ast3.Compare, typed_ast3.Lt),
            '<': (typed_ast3.Compare, typed_ast3.Lt),
            '.le.': (typed_ast3.Compare, typed_ast3.LtE),
            '<=': (typed_ast3.Compare, typed_ast3.LtE),
            '.gt.': (typed_ast3.Compare, typed_ast3.Gt),
            '>': (typed_ast3.Compare, typed_ast3.Gt),
            '.ge.': (typed_ast3.Compare, typed_ast3.GtE),
            '>=': (typed_ast3.Compare, typed_ast3.GtE),
            # Is
            # IsNot
            # In
            # NotIn
            '.and.': (typed_ast3.BoolOp, typed_ast3.And),
            '.or.': (typed_ast3.BoolOp, typed_ast3.Or),
            # unary
            # '+': (typed_ast3.UnaryOp, typed_ast3.UAdd),
            # '-': (typed_ast3.UnaryOp, typed_ast3.USub),
            '.not.': (typed_ast3.UnaryOp, typed_ast3.Not),
            # Invert: (typed_ast3.UnaryOp, typed_ast3.Invert)
            }[node.attrib['operator'].lower()]

    def _array_constructor(self, node: ET.Element) -> typed_ast3.ListComp:
        value_nodes = node.findall('./value')
        values = []
        for value_node in value_nodes:
            value = self.transform_all_subnodes(value_node, warn=False)
            if not value:
                continue
            assert len(value) == 1
            values.append(value[0])

        if len(values) != 1:
            raise NotImplementedError(
                'not implemented handling of {} in:\n{}'
                .format(values, ET.tostring(node).decode().rstrip()))

        header_node = node.find('./header')
        header = self.transform_all_subnodes(header_node, warn=False, ignored={'ac-implied-do-control'})
        assert len(header) == 1
        comp_target, comp_iter = header[0]
        generator = typed_ast3.comprehension(
            target=comp_target, iter=comp_iter, ifs=[], is_async=0)
        return typed_ast3.ListComp(elt=values[0], generators=[generator])

    def _array_constructor_values(self, node: ET.Element) -> typed_ast3.List:
        value_nodes = node.findall('./value')
        values = []
        for value_node in value_nodes:
            value = self.transform_all_subnodes(value_node, warn=False)
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
        return self.transform_all_subnodes(node, warn=False, ignored={'array-spec'})

    def _dimension(self, node: ET.Element) -> t.Union[typed_ast3.Index, typed_ast3.Slice]:
        dim_type = node.attrib['type']
        if dim_type == 'simple':
            values = self.transform_all_subnodes(node, ignored={'array-spec-element'})
            if len(values) != 1:
                _LOG.error('simple dimension should have exactly one value, but it has %i',
                           len(values))
            return typed_ast3.Index(value=values[0])
        elif dim_type == 'range':
            ranges = self.transform_all_subnodes(node, warn=False, ignored={'array-spec-element'})
            assert len(ranges) == 1, ranges
            return ranges[0]
        elif dim_type == 'assumed-shape':
            return typed_ast3.Slice(lower=None, upper=None, step=None)
        elif dim_type == 'upper-bound-assumed-shape':
            args = self.transform_all_subnodes(node, warn=False, ignored={'array-spec-element'})
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
        length = \
            self.transform(node.find('./length')) if node.attrib['hasLength'] == 'true' else None
        kind = self.transform(node.find('./kind')) if node.attrib['hasKind'] == 'true' else None
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
            return typed_ast3.parse(FORTRAN_PYTHON_TYPE_PAIRS[name, t.Any], mode='eval')
        elif length is not None:
            self._ensure_top_level_import('numpy', 'np')
            return typed_ast3.parse(FORTRAN_PYTHON_TYPE_PAIRS[name, length], mode='eval')
        elif kind is not None:
            self._ensure_top_level_import('numpy', 'np')
            if isinstance(kind, typed_ast3.Num):
                kind = kind.n
            if not isinstance(kind, int):
                #_LOG.warning('%s', ET.tostring(node).decode().rstrip())
                #raise NotImplementedError('non-literal kinds are not supported')
                python_type = typed_ast3.parse(FORTRAN_PYTHON_TYPE_PAIRS[name, None], mode='eval')
                self._ensure_top_level_import('static_typing', 'st')
                static_type = typed_ast3.Attribute(
                    value=typed_ast3.Name(id='st', ctx=typed_ast3.Load()),
                    attr=python_type, ctx=typed_ast3.Load())
                return typed_ast3.Subscript(
                    value=static_type, slice=typed_ast3.Index(value=kind), ctx=typed_ast3.Load())
                #typed_ast3.parse({
                #    'integer': 'st.int[0]'.format(kind),
                #    'real': lambda kind: 'st.float[0]'.format(kind)}[name](kind), mode='eval')
                #custom_kind_type.
                #return custom_kind_type
            return typed_ast3.parse(FORTRAN_PYTHON_TYPE_PAIRS[name, kind], mode='eval')
        else:
            return typed_ast3.parse(FORTRAN_PYTHON_TYPE_PAIRS[name, None], mode='eval')
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
            values = self.transform_all_subnodes(value_node, warn=False, ignored={'initialization'})
            assert len(values) == 1, values
            value = values[0]
        variable = typed_ast3.Name(id=node.attrib['name'])
        metadata = {}
        dimensions_node = node.find('./dimensions')
        if dimensions_node is not None:
            metadata['dimensions'] = self.transform(dimensions_node, warn=False)
        if metadata:
            variable.fortran_metadata = metadata
        return variable, value

    def _names(self, node: ET.Element) -> typed_ast3.arguments:
        return self._arguments(node)

    def _intrinsic_identity(self, call):
        return call

    def _intrinsic_getenv(self, call):
        assert isinstance(call, typed_ast3.Call), type(call)
        assert len(call.args) == 2, call.args
        self._ensure_top_level_import('os')
        target = call.args[1]
        if isinstance(target, typed_ast3.keyword):
            target = target.value
        return typed_ast3.Assign(
            targets=[target],
            value=typed_ast3.Subscript(
                value=typed_ast3.Attribute(value=typed_ast3.Name(id='os', ctx=typed_ast3.Load()),
                                           attr='environ', ctx=typed_ast3.Load()),
                slice=typed_ast3.Index(value=call.args[0]), ctx=typed_ast3.Load())
            , type_comment=None)

    def _intrinsic_count(self, call):
        assert isinstance(call, typed_ast3.Call), type(call)
        assert len(call.args) == 1, call.args
        return typed_ast3.Call(
            func=typed_ast3.Attribute(value=call.args[0], attr='sum', ctx=typed_ast3.Load()),
            args=[], keywords=[])

    def _intrinsic_converter_not_implemented(self, call):
        raise NotImplementedError(
            "cannot convert intrinsic call from raw AST:\n{}"
            .format(typed_astunparse.unparse(call)))

    def _intrinsic_numpy_call(self, call, name=None):
        if name is None:
            name = call.func.id
        return typed_ast3.Call(
            func=typed_ast3.Attribute(value=typed_ast3.Name(id='np', ctx=typed_ast3.Load()),
                                      attr=name, ctx=typed_ast3.Load()),
            args=call.args, keywords=call.keywords)

    _intrinsics_converters = {
        # Fortran 77
        'abs': _intrinsic_identity, # np.absolute
        'acos': _intrinsic_converter_not_implemented,
        'aimag': _intrinsic_converter_not_implemented,
        'aint': _intrinsic_converter_not_implemented,
        'anint': _intrinsic_converter_not_implemented,
        'asin': _intrinsic_converter_not_implemented,
        'atan': _intrinsic_converter_not_implemented,
        'atan2': _intrinsic_converter_not_implemented,
        'char': _intrinsic_converter_not_implemented,
        'cmplx': _intrinsic_converter_not_implemented,
        'conjg': _intrinsic_converter_not_implemented,
        'cos': _intrinsic_numpy_call,
        'cosh': _intrinsic_converter_not_implemented,
        'dble': _intrinsic_converter_not_implemented,
        'dim': _intrinsic_converter_not_implemented,
        'dprod': _intrinsic_converter_not_implemented,
        'exp': _intrinsic_converter_not_implemented,
        'ichar': _intrinsic_converter_not_implemented,
        'index': _intrinsic_converter_not_implemented,
        'int': _intrinsic_identity,
        'len': _intrinsic_converter_not_implemented,
        'lge': _intrinsic_converter_not_implemented,
        'lgt': _intrinsic_converter_not_implemented,
        'lle': _intrinsic_converter_not_implemented,
        'llt': _intrinsic_converter_not_implemented,
        'log': _intrinsic_converter_not_implemented,
        'log10': _intrinsic_converter_not_implemented,
        'max': functools.partial(_intrinsic_numpy_call, name='maximum'),
        'min': functools.partial(_intrinsic_numpy_call, name='minimum'),
        'mod': _intrinsic_converter_not_implemented,
        'nint': _intrinsic_converter_not_implemented,
        'real': _intrinsic_converter_not_implemented,
        'sign': _intrinsic_converter_not_implemented,
        'sin': _intrinsic_numpy_call,
        'sinh': _intrinsic_converter_not_implemented,
        'sqrt': _intrinsic_numpy_call,
        'tan': _intrinsic_converter_not_implemented,
        'tanh': _intrinsic_converter_not_implemented,
        # non-standard Fortran 77
        'getenv': _intrinsic_getenv,
        # Fortran 90
        # Character string functions
        'achar': _intrinsic_converter_not_implemented,
        'adjustl': _intrinsic_converter_not_implemented,
        'adjustr': _intrinsic_converter_not_implemented,
        'iachar': _intrinsic_converter_not_implemented,
        'len_trim': _intrinsic_converter_not_implemented,
        'repeat': _intrinsic_converter_not_implemented,
        'scan': _intrinsic_converter_not_implemented,
        'trim': lambda self, call: typed_ast3.Call(
            func=typed_ast3.Attribute(value=call.args[0], attr='rstrip', ctx=typed_ast3.Load()),
            args=call.args[1:], keywords=[]),
        'verify': _intrinsic_converter_not_implemented,
        # Logical function
        'logical': _intrinsic_converter_not_implemented,
        # Numerical inquiry functions
        'digits': _intrinsic_converter_not_implemented,
        'epsilon': _intrinsic_converter_not_implemented,
        'huge': _intrinsic_converter_not_implemented,
        'maxexponent': _intrinsic_converter_not_implemented,
        'minexponent': _intrinsic_converter_not_implemented,
        'precision': _intrinsic_converter_not_implemented,
        'radix': _intrinsic_converter_not_implemented,
        'range': _intrinsic_converter_not_implemented,
        'tiny': _intrinsic_converter_not_implemented,
        # Bit inquiry function
        'bit_size': _intrinsic_converter_not_implemented,
        # Vector- and matrix-multiplication functions
        'dot_product': functools.partial(_intrinsic_numpy_call, name='dot'),
        'matmul': _intrinsic_converter_not_implemented,
        # Array functions
        'all': _intrinsic_converter_not_implemented,
        'any': _intrinsic_converter_not_implemented,
        'count': _intrinsic_count,
        'maxval': _intrinsic_converter_not_implemented,
        'minval': _intrinsic_converter_not_implemented,
        'product': _intrinsic_converter_not_implemented,
        'sum': _intrinsic_identity,
        # Array location functions
        'maxloc': functools.partial(_intrinsic_numpy_call, name='argmax'),
        'minloc':  functools.partial(_intrinsic_numpy_call, name='argmin'),
        # Fortran 95
        'cpu_time': _intrinsic_converter_not_implemented,
        'present': _intrinsic_converter_not_implemented,
        'set_exponent': _intrinsic_converter_not_implemented,
        # Fortran 2003
        # Fortran 2008
        }

    def _name(self, node: ET.Element) -> typed_ast3.AST:
        name_str = node.attrib['id']
        name = typed_ast3.Name(id=name_str, ctx=typed_ast3.Load())
        name_str = name_str.lower()
        name_type = node.attrib['type'] if 'type' in node.attrib else None
        is_intrinsic = name_str in self._intrinsics_converters

        subscripts_node = node.find('./subscripts')
        try:
            args = self._args(subscripts_node) if subscripts_node else []
            call = typed_ast3.Call(func=name, args=args, keywords=[])
            if is_intrinsic:
                name_type = "function"
                call = self._intrinsics_converters[name_str](self, call)
        except SyntaxError:
            _LOG.info('transforming name to call failed as below (continuing despite that)', exc_info=True)

        slice_ = self._subscripts(subscripts_node) if subscripts_node else None
        subscript = typed_ast3.Subscript(value=name, slice=slice_, ctx=typed_ast3.Load())

        if name_type in ("procedure", "function"):
            return call
        elif not subscripts_node:
            return name
        elif name_type in ("variable",):
            return subscript
        elif not slice_:
            return call
        elif name_type in ("ambiguous",):
            return subscript
        elif name_type is not None:
            raise NotImplementedError('unrecognized name type "{}" in:\n{}'.format(name_type, ET.tostring(node).decode().rstrip()))
        elif name_type is None:
            raise NotImplementedError('no name type in:\n{}'.format(ET.tostring(node).decode().rstrip()))
        raise NotImplementedError('not implemented handling of:\n{}'.format(ET.tostring(node).decode().rstrip()))

    def _args(self, node: ET.Element, arg_node_name: str = 'subscript') -> t.List[typed_ast3.AST]:
        args = []
        for arg_node in node.findall(f'./{arg_node_name}'):
            new_args = self.transform_all_subnodes(arg_node, warn=False, skip_empty=True)
            if not new_args:
                continue
            if len(new_args) != 1:
                raise SyntaxError(
                    'args must be specified one new arg at a time, not like {} in:\n{}'.format(
                        [typed_astunparse.unparse(_) for _ in new_args],
                        ET.tostring(arg_node).decode().rstrip()))
            args += new_args
        return args

    def _subscripts(
            self, node: ET.Element) -> t.Union[
                typed_ast3.Index, typed_ast3.Slice, typed_ast3.ExtSlice]:
        subscripts = []
        for subscript in node.findall('./subscript'):
            new_subscripts = self.transform_all_subnodes(subscript, warn=False)
            if not new_subscripts:
                continue
            if len(new_subscripts) == 1:
                new_subscript = typed_ast3.Index(value=new_subscripts[0])
            elif len(new_subscripts) == 2:
                new_subscript = typed_ast3.Slice(
                    lower=new_subscripts[0], upper=new_subscripts[1], step=None)
            else:
                _LOG.error('%s', ET.tostring(subscript).decode().rstrip())
                _LOG.error('%s', [typed_astunparse.unparse(_) for _ in new_subscripts])
                raise SyntaxError('there must be 1 or 2 new subscript data elements')
            subscripts.append(new_subscript)
        if len(subscripts) == 1:
            return subscripts[0]
        elif len(subscripts) > 1:
            return typed_ast3.ExtSlice(dims=subscripts)
        return []  # TODO: TMP
        raise SyntaxError(
            'subscripts node must contain at least one "subscript" node:\n{}'
            .format(ET.tostring(node).decode().rstrip()))

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
