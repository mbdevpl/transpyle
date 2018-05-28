"""Generalizing C++ AST."""

import logging
import xml.etree.ElementTree as ET

import typed_ast.ast3 as typed_ast3

from ..general import XmlAstGeneralizer
from ..general.ast_generalizer import ContinueIteration
from .definitions import CPP_PYTHON_TYPE_PAIRS

_LOG = logging.getLogger(__name__)


class CppAstGeneralizer(XmlAstGeneralizer):

    """Transform C++ XML AST generated with CastXML into Python AST from typed_ast."""

    def __init__(self, scope=None):
        super().__init__(scope)
        assert scope is not None, \
            'scope={"path": pathlib.Path(...)} has to be provided for C++ generalizer'
        self.file_id = None
        self.fundamental_types = {}

    def _CastXML(self, node: ET.Element):  # pylint: disable=invalid-name
        file_nodes = self.get_all(node, './File')
        relevant_file_nodes = []
        parsed_filename = str(self.scope['path'])
        for file_node in file_nodes:
            name = file_node.attrib['name']
            # if name.startswith('/usr') or name == '<builtin>':
            if name != parsed_filename:
                continue
            relevant_file_nodes.append(file_node)
        assert len(relevant_file_nodes) == 1, relevant_file_nodes
        file_node = relevant_file_nodes[0]
        self.file_id = file_node.attrib['id']

        types = {'ArrayType', 'CvQualifiedType', 'ElaboratedType', 'FunctionType',
                 'FundamentalType', 'MethodType', 'OffsetType', 'PointerType', 'ReferenceType'}

        for type_ in ['FundamentalType', 'PointerType']:
            type_nodes = self.get_all(node, './{}'.format(type_))
            self.fundamental_types.update(dict(self.transform_all(type_nodes, parent=node)))
        import pprint
        _LOG.warning('Detected types:\n%s', pprint.pformat(
            {k: typed_ast3.dump(v) for k, v in self.fundamental_types.items()}))

        body = self.transform_all_subnodes(node, ignored={'Namespace', 'File'} | types)
        return typed_ast3.Module(body=body, type_ignores=[])

    def default(self, node: ET.Element):
        """Ignore irrelevant nodes, raise error otherwise."""
        if 'file' not in node.attrib:
            _LOG.warning('no file for %s', node)
            # self.no_transform(node)
            raise ContinueIteration()
        if node.attrib['file'] != self.file_id:
            raise ContinueIteration()
        self.no_transform(node)

    _Class = default
    _Field = default
    _Constructor = default
    _Destructor = default
    _Method = default
    _OperatorMethod = default

    _Variable = default
    _Typedef = default
    _Enumeration = default
    _Struct = default
    _Union = default
    _OperatorFunction = default
    _Converter = default

    def _Unimplemented(self, node: ET.Element):  # pylint: disable=invalid-name
        try:
            node_str = node.attrib['kind']
        except KeyError:
            _LOG.warning('unexpected behavior')
            try:
                node_str = node.attrib['type_class']
            except KeyError:
                self.no_transform(node)
        _LOG.warning('the underlying CastXML parser did not parse a %s', node_str)
        raise ContinueIteration()

    def _Function(self, node: ET.Element):  # pylint: disable=invalid-name
        if node.attrib['file'] != self.file_id:
            raise ContinueIteration()
        name = node.attrib['name']
        arguments = typed_ast3.arguments(args=self.transform_all_subnodes(node), vararg=None,
                                         kwonlyargs=[], kwarg=None, defaults=[], kw_defaults=[])
        body = [typed_ast3.Ellipsis()]
        returns = typed_ast3.NameConstant(None)
        return typed_ast3.FunctionDef(name=name, args=arguments, body=body, decorator_list=[],
                                      returns=returns)

    def _Argument(self, node: ET.Element):  # pylint: disable=invalid-name
        annotation = self.fundamental_types[node.attrib['type']]
        assert annotation is not None
        #import ipdb; ipdb.set_trace()
        return typed_ast3.arg(arg=node.attrib['name'], annotation=annotation)

    def _FundamentalType(self, node: ET.Element):  # pylint: disable=invalid-name
        id_ = node.attrib['id']
        name = node.attrib['name']
        return (id_, typed_ast3.parse(CPP_PYTHON_TYPE_PAIRS[name], mode='eval').body)

    def _PointerType(self, node: ET.Element):  # pylint: disable=invalid-name
        id_ = node.attrib['id']
        type_ = node.attrib['type']
        is_const = type_.endswith('c')
        if is_const:
            type_ = type_[:-1]
        try:
            base_type = self.fundamental_types[type_]
        except KeyError:
            # _LOG.debug()
            base_type = type_
        type_info = typed_ast3.Subscript(
            value=typed_ast3.Name(id='Pointer', ctx=typed_ast3.Load()), slice=base_type)
        if is_const:
            type_info = typed_ast3.Subscript(
                value=typed_ast3.Name(id='Const', ctx=typed_ast3.Load()), slice=type_info)
        return (id_, type_info)
