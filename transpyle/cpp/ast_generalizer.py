"""Generalizing C++ AST."""

import logging
# import typing as t
import xml.etree.ElementTree as ET

import typed_ast.ast3 as typed_ast3

from ..general import Language, XmlAstGeneralizer
from ..general.ast_generalizer import ContinueIteration
from .definitions import CPP_PYTHON_TYPE_PAIRS

_LOG = logging.getLogger(__name__)


class CppAstGeneralizer(XmlAstGeneralizer):

    """Transform C++ XML AST generated with CastXML into Python AST from typed_ast."""

    def __init__(self):
        super().__init__(Language.find('C++'))
        self.file_id = None
        self.fundamental_types = {}

    def _CastXML(self, node: ET.Element):
        file_nodes = self.get_all(node, './File')
        relevant_file_nodes = []
        for file_node in file_nodes:
            name = file_node.attrib['name']
            if name.startswith('/usr') or name == '<builtin>':
                continue
            relevant_file_nodes.append(file_node)
        assert len(relevant_file_nodes) == 1, relevant_file_nodes
        file_node = relevant_file_nodes[0]
        self.file_id = file_node.attrib['id']

        types = {'FundamentalType', 'PointerType', 'CvQualifiedType', 'ArrayType',
                 'ElaboratedType', 'ReferenceType', 'FunctionType'}
        type_nodes = self.get_all(node, './FundamentalType')

        self.fundamental_types = {
            type_node.attrib['id']: self.transform_all(type_node, parent=node)
            for type_node in type_nodes}

        body = self.transform_all_subnodes(node, ignored={'Namespace', 'File'} | types)
        return typed_ast3.Module(body=body, type_ignores=[])

    def default(self, node: ET.Element):
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

    def _Unimplemented(self, node: ET.Element):
        _LOG.warning('the underlying CastXML parser did not parse a %s', node.attrib['kind'])
        raise ContinueIteration()

    def _Function(self, node: ET.Element):
        if node.attrib['file'] != self.file_id:
            raise ContinueIteration()
        name = node.attrib['name']
        arguments = typed_ast3.arguments(args=self.transform_all_subnodes(node), vararg=None,
                                         kwonlyargs=[], kwarg=None, defaults=[], kw_defaults=[])
        body = [typed_ast3.Ellipsis()]
        returns = typed_ast3.NameConstant(None)
        return typed_ast3.FunctionDef(name=name, args=arguments, body=body, decorator_list=[],
                                      returns=returns)

    def _Argument(self, node: ET.Element):
        return typed_ast3.arg(arg=node.attrib['name'], annotation=None)

    def _FundamentalType(self, node: ET.Element):
        name = node.attrib['name']
        return typed_ast3.parse(CPP_PYTHON_TYPE_PAIRS[name], mode='eval')
        # self.no_transform(node)
