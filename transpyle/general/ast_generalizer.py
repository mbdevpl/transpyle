"""Generailzation of language-specific ASTs."""

import logging
import typing as t
import xml.etree.ElementTree as ET

import typed_ast.ast3 as typed_ast3

from .registry import Registry
from .language import Language

_LOG = logging.getLogger(__name__)


class ContinueIteration(StopIteration):

    pass


class AstGeneralizer(Registry):

    """Generalize a language-specific AST."""

    def __init__(self, language: Language):
        self.language = language

    def generalize(self, tree):
        """Generalize a language-specific AST into a general one."""
        raise NotImplementedError()


class IdentityAstGeneralizer(AstGeneralizer):

    """Do nothing with the AST."""

    def generalize(self, tree):
        return tree


class XmlAstGeneralizer(AstGeneralizer):

    """Generalize an XML-based AST."""

    def __init__(self, language: Language):
        super().__init__(language)

        self._top_level_imports = dict()
        self._transforms = [f for f in dir(self) if not f.startswith('__')]

    def _ensure_top_level_import(self, canonical_name: str, alias: t.Optional[str] = None):
        if (canonical_name, alias) not in self._top_level_imports:
            if canonical_name in ('mpif.h', '?'):  # TODO: other ways to include MPI?
                self._ensure_mpi_import(canonical_name, alias)
            else:
                self._top_level_imports[canonical_name, alias] = [typed_ast3.Import(
                    names=[typed_ast3.alias(name=canonical_name, asname=alias)])]

    def _ensure_mpi_import(self, canonical_name, alias):
        # if ('mpi4py', None) not in self._top_level_imports:
        self._top_level_imports[canonical_name, alias] = [
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

    def generalize(self, tree: ET.Element):
        return self.transform_one(tree)

    def no_transform(self, node: ET.Element):
        raise NotImplementedError(
            'not implemented handling of:\n{}'.format(ET.tostring(node).decode().rstrip()))

    def transform_one(self, node: ET.Element, warn: bool = True, ignored: t.Set[str] = None,
                      parent: t.Optional[ET.Element] = None):
        """Transform a single node."""
        assert node is not None
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
            _LOG.warning('ignoring existing transformer for %s', node.tag)
            raise ContinueIteration()
        _transform = getattr(self, transform_name)
        return _transform(node)

    def transform_all(self, nodes: t.List[ET.Element], warn: bool = True, skip_empty: bool = False,
                      ignored: t.Set[str] = None, parent: t.Optional[ET.Element] = None) -> list:
        """Transform all nodes in a given list."""
        transformed = []
        for node in nodes:
            assert node is not None
            if skip_empty and not node.attrib and len(node) == 0:
                continue
            try:
                transformed.append(self.transform_one(node, warn, ignored, parent))
            except ContinueIteration:
                continue
        return transformed

    def transform_all_subnodes(
            self, node: ET.Element, warn: bool = True, skip_empty: bool = False,
            ignored: t.Set[str] = None):
        """Transform all subnodes of a given node."""
        assert node is not None
        return self.transform_all(iter(node), warn, skip_empty, ignored, node)
