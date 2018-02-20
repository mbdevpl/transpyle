"""Generailzation of language-specific ASTs."""

import collections.abc
import itertools
import logging
import typing as t
import xml.etree.ElementTree as ET

import typed_ast.ast3 as typed_ast3

from .exc import ContinueIteration
from .misc import flatten_syntax
from .registry import Registry

_LOG = logging.getLogger(__name__)


class AstGeneralizer(Registry):

    """Generalize a language-specific AST."""

    def __init__(self, scope=None):
        """Scope, if provided, should limit the generalization process to the given criteria."""
        self.scope = scope

    def generalize(self, syntax):
        """Generalize a language-specific AST into a general one."""
        raise NotImplementedError()


class IdentityAstGeneralizer(AstGeneralizer):

    """Do nothing with the AST, i.e. assume it already is generalized."""

    def __init__(self):
        super().__init__(None)

    def generalize(self, syntax):
        return syntax


class XmlAstGeneralizer(AstGeneralizer):

    """Generalize an XML-based AST.

    Limitation of XML node name recognition: dash '-' and underscore '_' are not differentiated,
    therefore <some_node> and <some-node> will be handled by the same handler (i.e. _some_node)
    """

    def __init__(self, scope=None, case_sensitive: bool = False):
        super().__init__(scope)
        self.case_sensitive = case_sensitive
        self._transforms = [f for f in dir(self) if f.startswith('_') and not f.startswith('__')]
        self._import_statements = dict()

    @property
    def import_statements(self):
        return list(itertools.chain(*[statements
                                      for _, statements in self._import_statements.items()]))

    def ensure_import(self, canonical_name: str, alias: t.Optional[str] = None):
        if (canonical_name, alias) not in self._import_statements:
            if canonical_name in ('mpif.h', '?'):  # TODO: other ways to include MPI?
                self.ensure_mpi(canonical_name, alias)
            else:
                self._import_statements[canonical_name, alias] = [typed_ast3.Import(
                    names=[typed_ast3.alias(name=canonical_name, asname=alias)])]

    def ensure_mpi(self, canonical_name, alias):
        # if ('mpi4py', None) not in self._import_statements:
        self._import_statements[canonical_name, alias] = [
            typed_ast3.ImportFrom(
                module='mpi4py', names=[typed_ast3.alias(name='MPI', asname=None)], level=0),
            # typed_ast3.parse('mpi4py.config = no_auto_init', mode='eval') # TODO: may be needed
            ]

    def get_one(self, node: ET.Element, xpath: str) -> ET.Element:
        found = node.find(xpath)
        if found is None:
            raise SyntaxError('no "{}" found in "{}":\n{}'
                              .format(xpath, node.tag, ET.tostring(node).decode().rstrip()))
        return found

    def get_all(self, node: ET.Element, xpath: str,
                require_results: bool = True) -> t.List[ET.Element]:
        found = node.findall(xpath)
        if require_results and not found:
            raise SyntaxError('not a single "{}" found in "{}":\n{}'
                              .format(xpath, node.tag, ET.tostring(node).decode().rstrip()))
        return found

    def generalize(self, syntax: ET.Element):
        self._import_statements = dict()
        return self.transform_one(syntax)

    def no_transform(self, node: ET.Element):
        raise NotImplementedError(
            'not implemented handling of:\n{}'.format(ET.tostring(node).decode().rstrip()))

    def transform_one(self, node: ET.Element, warn: bool = False, ignored: t.Set[str] = None,
                      parent: t.Optional[ET.Element] = None):
        """Transform a single node."""
        assert isinstance(node, ET.Element), type(node)
        transform_name = '_{}'.format(node.tag.replace('-', '_'))
        if transform_name not in self._transforms:
            if ignored and node.tag in ignored:
                raise ContinueIteration()
            if warn:
                if parent is None:
                    _LOG.warning('no transformer available for node "%s"', node.tag)
                else:
                    _LOG.warning('no transformer available for node "%s", a subnode of "%s"',
                                 node.tag, parent.tag)
                _LOG.debug('%s', ET.tostring(node).decode().rstrip())
                raise ContinueIteration()
            if parent is None:
                raise NotImplementedError('no transformer available for node "{}":\n{}'
                                          .format(node.tag, ET.tostring(node).decode().rstrip()))
            else:
                raise NotImplementedError(
                    'no transformer available for node "{}", a subnode of "{}":\n{}'
                    .format(node.tag, parent.tag, ET.tostring(node).decode().rstrip()))
        if ignored and node.tag in ignored:
            _LOG.info('ignoring existing transformer for %s', node.tag)
            raise ContinueIteration()
        _transform = getattr(self, transform_name)
        transformed = _transform(node)
        flatten_syntax(transformed)
        return transformed

    def transform_all(
            self, nodes: t.Iterable[ET.Element], warn: bool = False, skip_empty: bool = False,
            ignored: t.Set[str] = None, parent: t.Optional[ET.Element] = None) -> list:
        """Transform all nodes in a given list."""
        assert isinstance(nodes, (ET.Element, collections.abc.Iterable)), type(nodes)
        transformed = []
        for node in nodes:
            assert isinstance(node, ET.Element), type(node)
            if skip_empty and not node.attrib and len(node) == 0:
                continue
            try:
                transformed.append(self.transform_one(node, warn, ignored, parent))
            except ContinueIteration:
                continue
        flatten_syntax(transformed)
        return transformed

    def transform_all_subnodes(
            self, node: ET.Element, warn: bool = False, skip_empty: bool = False,
            ignored: t.Set[str] = None) -> list:
        """Transform all subnodes of a given node."""
        assert isinstance(node, ET.Element), type(node)
        return self.transform_all(node, warn, skip_empty, ignored, node)
