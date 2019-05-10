"""Generalizing C++ AST."""

import logging
import pprint
# import re
import typing as t
import xml.etree.ElementTree as ET

import horast
from static_typing.ast_manipulation import RecursiveAstTransformer
import typed_ast.ast3 as typed_ast3

from ..general import XmlAstGeneralizer
from ..general.exc import ContinueIteration, AstGeneralizationError
from .definitions import CPP_PYTHON_TYPE_PAIRS, CPP_PYTHON_CLASS_PAIRS, CPP_STL_CLASSES

NAMESPACE_NODES = {'Namespace'}

TYPE_NODES = {'ArrayType', 'CvQualifiedType', 'ElaboratedType', 'FunctionType',
              'FundamentalType', 'MethodType', 'OffsetType', 'PointerType', 'ReferenceType',
              'Struct', 'Class', 'Typedef'}

RESOLVED_TYPE_NODES = ['FundamentalType', 'PointerType', 'ElaboratedType', 'Struct', 'Class']

IGNORED_NODES = {'File'} | NAMESPACE_NODES | TYPE_NODES

_LOG = logging.getLogger(__name__)


def make_pointer(base_type: typed_ast3.AST):
    return typed_ast3.Subscript(
        value=typed_ast3.Name(id='Pointer', ctx=typed_ast3.Load()),
        slice=typed_ast3.Index(base_type), ctx=typed_ast3.Load())


def make_const(base_type: typed_ast3.AST):
    return typed_ast3.Subscript(
        value=typed_ast3.Name(id='Const', ctx=typed_ast3.Load()),
        slice=typed_ast3.Index(base_type), ctx=typed_ast3.Load())


class XmlAstGeneralizationError(AstGeneralizationError):

    def __init__(self, generalizer: XmlAstGeneralizer, xml_node: ET.Element):
        assert isinstance(generalizer, XmlAstGeneralizer), type(generalizer)
        assert isinstance(xml_node, ET.Element), type(xml_node)
        self.generalizer = generalizer
        self.xml_node = xml_node
        super().__init__(ET.tostring(xml_node).decode().rstrip())


def diagnose(function):
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except AstGeneralizationError as error:
            raise XmlAstGeneralizationError(*args, **kwargs) from error
        except KeyError as error:
            raise XmlAstGeneralizationError(*args, **kwargs) from error
    return wrapper


class CastXMLTypeFinder(XmlAstGeneralizer):

    """Produce Python type hierarchy for C++ AST generated with CastXML."""

    def __init__(self, scope=None):
        super().__init__(scope)
        assert scope is not None, \
            'scope={\'path\': pathlib.Path(...)} has to be provided for C++ generalizer'
        self.file_id = None
        self._new_relevant_types = None
        self.initialize()

    def initialize(self):
        self.file_id = None
        self.namespaces = {}
        self.all_types = {}
        self.relevant_types = {}
        self.resolved_types = {}

    def _determine_file_id(self, root_node: ET.Element) -> str:
        file_nodes = self.get_all(root_node, './File')
        relevant_file_nodes = []
        parsed_filename = str(self.scope['path'])
        for file_node in file_nodes:
            name = file_node.attrib['name']
            if name != parsed_filename:
                continue
            relevant_file_nodes.append(file_node)
        assert len(relevant_file_nodes) == 1, relevant_file_nodes
        file_node = relevant_file_nodes[0]
        return file_node.attrib['id']

    def is_relevant(self, node: ET.Element):
        try:
            return node.attrib['file'] == self.file_id
        except KeyError:
            return False

    def _CastXML(self, node: ET.Element):  # pylint: disable=invalid-name
        self.file_id = self._determine_file_id(node)
        self.find_types(node)

        while self._new_relevant_types:
            _LOG.debug('there are %i new relevant types', len(self._new_relevant_types))
            self.relevant_types.update(self._new_relevant_types)
            self._new_relevant_types = {}
            new_resolved_types = {}
            for id_, node_ in self.relevant_types.items():
                if id_ in self.resolved_types:
                    continue
                new_resolved_types[id_] = self.transform_one(node_)
                _LOG.debug('resolved %s into %s', ET.tostring(node_).decode().rstrip(),
                           horast.unparse(new_resolved_types[id_]))
            self.resolved_types.update(new_resolved_types)

        self._fix_resolved_types(self.resolved_types)

        _LOG.info('type resolution complete: %s', pprint.pformat(
            {_: horast.unparse(type_).strip() for _, type_ in self.resolved_types.items()}))

    def find_types(self, root_node: ET.Element) -> t.Tuple[dict, dict]:
        self._new_relevant_types = {}
        self.transform_all_subnodes(root_node, ignored={'File'} | TYPE_NODES)
        for type_ in TYPE_NODES:
            for node in self.get_all(root_node, './{}'.format(type_), require_results=False):
                id_ = node.attrib['id']
                self.all_types[node.attrib['id']] = node
                if id_ not in self._new_relevant_types:
                    continue
                self._new_relevant_types[node.attrib['id']] = node
        assert all(v is not None for v in self._new_relevant_types.values()), \
            self._new_relevant_types
        _LOG.info('found %i relevant types (out of %i) in "%s"',
                  len(self._new_relevant_types), len(self.all_types), self.scope['path'])

    def _fix_resolved_types(self, resolved_types: dict) -> None:
        resolver = CastXMLTypeResolver(resolved_types=resolved_types)
        resolver.modified = True
        while resolver.modified:
            resolver.modified = False
            for _, type_ in resolved_types.items():
                resolver.visit(type_)
        if resolver.unresolved_types:
            _LOG.error('after type resolution for "%s", %i types remain unresolved',
                       self.scope['path'], len(resolver.unresolved_types))
            _LOG.debug('the following types remain unresolved:\n%s',
                       pprint.pformat(resolver.unresolved_types))
            raise NotImplementedError(
                'could not resolve some types: {}'.format(resolver.unresolved_types))

    def default(self, node: ET.Element):
        """Ignore irrelevant nodes, raise error otherwise."""
        if not self.is_relevant(node):
            # _LOG.warning('no file for %s', ET.tostring(node).decode().rstrip())
            # self.no_transform(node)
            raise ContinueIteration()
        self.no_transform(node)

    _Unimplemented = default

    _Field = default
    _Constructor = default
    _Destructor = default
    _Method = default
    _OperatorMethod = default

    _Variable = default
    _Enumeration = default
    _Union = default
    _OperatorFunction = default
    _Converter = default

    def _Function(self, node: ET.Element):  # pylint: disable=invalid-name
        if not self.is_relevant(node):
            raise ContinueIteration()
        self.transform_all_subnodes(node)
        self._new_relevant_types[node.attrib['returns']] = None

    def _Argument(self, node: ET.Element):  # pylint: disable=invalid-name
        self._new_relevant_types[node.attrib['type']] = None

    @diagnose
    def _Namespace(self, node: ET.Element):  # pylint: disable=invalid-name
        id_ = node.attrib['id']
        if 'name' not in node.attrib:
            _LOG.info('ignoring namespace without name')
            return
        self.namespaces[id_] = node.attrib['name']

    def _FundamentalType(self, node: ET.Element):  # pylint: disable=invalid-name
        name = node.attrib['name']
        return typed_ast3.parse(CPP_PYTHON_TYPE_PAIRS[name], mode='eval').body

    def _PointerType(self, node: ET.Element):  # pylint: disable=invalid-name
        type_id = node.attrib['type']
        is_const = type_id.endswith('c')
        if is_const:
            type_id = type_id[:-1]
        assert type_id in self.all_types
        if type_id not in self.relevant_types and type_id not in self._new_relevant_types:
            self._new_relevant_types[type_id] = self.all_types[type_id]
            _LOG.debug('type makred as relevant through a pointer: %s',
                       ET.tostring(self.all_types[type_id]).decode().rstrip())
        type_info = make_pointer(typed_ast3.Str(type_id, ''))
        if is_const:
            type_info = make_const(type_info)
        return type_info

    '''
    def _ElaboratedType(self, node: ET.Element):  # pylint: disable=invalid-name
        id_ = node.attrib['id']
        type_ = node.attrib['type']
        try:
            base_type = self.fundamental_types[type_]
        except KeyError:
            # _LOG.debug()
            base_type = typed_ast3.Str(type_, '')
        type_info = typed_ast3.Subscript(
            value=typed_ast3.Name(id='Elaborated', ctx=typed_ast3.Load()),
            slice=typed_ast3.Index(base_type), ctx=typed_ast3.Load())
        return (id_, type_info)

    def _Struct(self, node: ET.Element):  # pylint: disable=invalid-name
        context = node.attrib['context']
        if context not in self._namespaces or self._namespaces[context].id != 'std':
            raise ContinueIteration()
        struct_name = node.attrib['name']
        full_name = '{}::{}'.format(context, struct_name)
        if struct_name.startswith('hash<') and struct_name.endswith('>'):
            raise ContinueIteration()
        if full_name in CPP_PYTHON_CLASS_PAIRS:
            id_ = node.attrib['id']
            return (id_, typed_ast3.Name(id=CPP_PYTHON_CLASS_PAIRS[full_name], ctx=typed_ast3.Load()))
        if struct_name.startswith('__'):
            raise ContinueIteration()
        self.no_transform(node)
    '''

    def _Class(self, node: ET.Element):  # pylint: disable=invalid-name
        context = node.attrib['context']
        assert context in self.namespaces, context

        cls_name = node.attrib['name']
        if '<' in cls_name:
            _LOG.warning('processing template class %s', cls_name)
            assert '>' in cls_name
            cls_name, _, rest = cls_name.partition('<')
            rest = rest[:-1]
            generic_args = [_.strip() for _ in rest.split(',')]
            _LOG.warning('found generic args: %s', generic_args)

        full_name = '{}::{}'.format(self.namespaces[context], cls_name)
        is_stl_class = full_name in CPP_STL_CLASSES and generic_args
        value_type = None

        body = []
        for member_id in node.attrib['members'].split():
            if not is_stl_class:
                # TODO: handle non-STL classes too
                break
            if member_id not in self.all_types:
                continue
            member_type = self.all_types[member_id]
            if member_type.tag == 'Typedef' and member_type.attrib['name'] == 'value_type':
                referenced_id = member_type.attrib['type']
                assert referenced_id in self.all_types
                if referenced_id not in self.relevant_types \
                        and referenced_id not in self._new_relevant_types:
                    self._new_relevant_types[referenced_id] = self.all_types[referenced_id]
                    _LOG.debug('type marked as relevant due to being container value type %s',
                               ET.tostring(self.all_types[referenced_id]).decode().rstrip())
                body.append(typed_ast3.Expr(typed_ast3.Str(referenced_id, '')))
                value_type = referenced_id
            '''
            if member_id not in self.relevant_types and member_id not in self._new_relevant_types:
                self._new_relevant_types[member_id] = member_type
                _LOG.warning('marked %s as relevant type',
                             ET.tostring(member_type).decode().rstrip())
            body.append(typed_ast3.Expr(typed_ast3.Str(member_id, '')))
            '''

        base_class = typed_ast3.parse(CPP_PYTHON_CLASS_PAIRS[full_name], mode='eval').body

        if is_stl_class:
            assert value_type is not None
            base_class = typed_ast3.Subscript(
                value=base_class,
                slice=typed_ast3.Index(typed_ast3.Str(value_type, '')), ctx=typed_ast3.Load())

        return base_class

    def _Base(self, node: ET.Element):
        return node.attrib['type']


class CastXMLTypeResolver(RecursiveAstTransformer[typed_ast3]):

    def __init__(self, *args, resolved_types, **kwargs):
        super().__init__(*args, **kwargs)
        self.resolved_types = resolved_types
        self.unresolved_types = set()
        self.modified = False

    def visit_node(self, node):
        if not isinstance(node, typed_ast3.Str):
            return node
        try:
            resolved_type = self.resolved_types[node.s]
        except KeyError:
            self.unresolved_types.add(node.s)
            _LOG.debug('cannot currently resolve %s', node.s)
            return node
        if node.s in self.unresolved_types:
            self.unresolved_types.remove(node.s)
        _LOG.debug('resolved %s into %s', node.s, typed_ast3.dump(resolved_type))
        self.modified = True
        return resolved_type


class CppAstGeneralizer(XmlAstGeneralizer):

    """Transform C++ XML AST generated with CastXML into Python AST from typed_ast."""

    def __init__(self, scope=None):
        super().__init__(scope)
        assert scope is not None, \
            'scope={"path": pathlib.Path(...)} has to be provided for C++ generalizer'
        self.types = CastXMLTypeFinder(self.scope)

    def _CastXML(self, node: ET.Element):  # pylint: disable=invalid-name
        self.types.initialize()
        self.types.generalize(node)

        body = self.transform_all_subnodes(node, ignored=IGNORED_NODES)
        return typed_ast3.Module(body=body, type_ignores=[])

    def default(self, node: ET.Element):
        """Ignore irrelevant nodes, raise error otherwise."""
        if not self.types.is_relevant(node):
            raise ContinueIteration()
        self.no_transform(node)

    _Field = default
    _Constructor = default
    _Destructor = default
    _Method = default
    _OperatorMethod = default

    _Variable = default
    _Enumeration = default
    _Union = default
    _OperatorFunction = default
    _Converter = default

    def _Unimplemented(self, node: ET.Element):  # pylint: disable=invalid-name
        try:
            node_str = node.attrib['kind']
        except KeyError:
            _LOG.debug('unexpected behavior: %s', ET.tostring(node).decode().rstrip())
            try:
                node_str = node.attrib['type_class']
            except KeyError:
                self.no_transform(node)
        _LOG.info('the underlying CastXML parser did not parse a %s', node_str)
        raise ContinueIteration()

    def _Function(self, node: ET.Element):  # pylint: disable=invalid-name
        if not self.types.is_relevant(node):
            raise ContinueIteration()
        name = node.attrib['name']
        arguments = typed_ast3.arguments(args=self.transform_all_subnodes(node), vararg=None,
                                         kwonlyargs=[], kwarg=None, defaults=[], kw_defaults=[])

        body = [typed_ast3.Expr(value=typed_ast3.Ellipsis())]
        returns = self.types.resolved_types[node.attrib['returns']]
        return typed_ast3.FunctionDef(name=name, args=arguments, body=body, decorator_list=[],
                                      returns=returns)

    def _Argument(self, node: ET.Element):  # pylint: disable=invalid-name
        try:
            annotation = self.types.resolved_types[node.attrib['type']]
        except KeyError as error:
            raise NotImplementedError('cannot generalize the node {}'.format(
                ET.tostring(node).decode().rstrip())) from error
        assert annotation is not None
        return typed_ast3.arg(arg=node.attrib['name'], annotation=annotation)

    def _Class(self, node: ET.Element):  # pylint: disable=invalid-name
        self.default(node)

        '''
        keywords = [typed_ast3.keyword(
            arg='generic_args',
            value=typed_ast3.Tuple([typed_ast3.Str(_, '') for _ in generic_args]))]

        bases = self.transform_all_subnodes(node)
        for base in bases:
            assert base in self.all_types
            if base not in self.relevant_types and base not in self._new_relevant_types:
                self._new_relevant_types[base] = self.all_types[base]
                _LOG.warning('marked %s as relevant type',
                             ET.tostring(self.all_types[base]).decode().rstrip())

        if not body:
            body = [typed_ast3.Pass()]

        return typed_ast3.ClassDef(name=cls_name, bases=bases, keywords=keywords, body=body,
                                   decorator_list=[])
        '''

        '''
        if cls_name.startswith('vector<') and cls_name.endswith('>'):
            _LOG.warning('processing class %s', ET.tostring(node).decode().rstrip())

            # vector&lt;double,
            return (id_, typed_ast3.Subscript(
                value=typed_ast3.Attribute(
                    value=typed_ast3.Name(id='t', ctx=typed_ast3.Load()),
                    attr='List', ctx=typed_ast3.Load()),
                slice=typed_ast3.Index(typed_ast3.Attribute(
                    value=typed_ast3.Name(id='np', ctx=typed_ast3.Load()),
                    attr='double', ctx=typed_ast3.Load())), ctx=typed_ast3.Load()))
        if re.fullmatch(r'[A-Za-z_]+', cls_name):
            return (id_, typed_ast3.Name(id=cls_name, ctx=typed_ast3.Load()))
        # import ipdb; ipdb.set_trace()
        # return self.default(node)
        #
        raise ContinueIteration()
        # _LOG.error('not really processing class %s', ET.tostring(node).decode().rstrip())
        # return (id_, typed_ast3.Str('class_{}'.format(node.attrib['name']), ''))
        '''
