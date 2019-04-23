
import collections.abc
import typing as t

import static_typing as st
import typed_ast.ast3 as typed_ast3


def syntax_name(syntax: typed_ast3.AST) -> str:
    """Return name of the syntax element, or raise TypeError if given syntax does not have any."""
    if isinstance(syntax, typed_ast3.Name):
        return syntax.id
    if isinstance(syntax, typed_ast3.ClassDef):
        return syntax.name
    if isinstance(syntax, typed_ast3.FunctionDef):
        return syntax.name
    if isinstance(syntax, typed_ast3.keyword):
        return syntax.arg
    if isinstance(syntax, typed_ast3.Attribute):
        return '{}.{}'.format(syntax_name(syntax.value), syntax.attr)
    raise TypeError('the AST type {} does not have a name'.format(type(syntax)))


class SyntaxFinder(st.ast_manipulation.RecursiveAstVisitor[typed_ast3]):

    """Find all AST nodes that match given criteria."""

    def __init__(self, types: t.Optional[tuple] = None, names: t.Optional[set] = None,
                 predicate: t.Optional[collections.abc.Callable] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert types is None or isinstance(types, tuple), type(types)
        assert names is None or isinstance(names, set), type(names)
        assert predicate is None or isinstance(predicate, collections.abc.Callable), type(predicate)
        self._found = []
        self._types = types
        self._names = names
        self._predicate = predicate

    @property
    def found(self):
        return self._found

    @property
    def found_any(self) -> bool:
        return len(self._found) > 0

    def satisfies_criteria(self, node) -> bool:
        return (
            self.satisfies_type_criteria(node) and self.satisfies_name_criteria(node)
            and (self._predicate is None or self._predicate(node)))

    def satisfies_type_criteria(self, node) -> bool:
        return self._types is None or isinstance(node, self._types)

    def satisfies_name_criteria(self, node) -> bool:
        try:
            return self._names is None or syntax_name(node) in self._names
        except TypeError:
            return False

    def visit_node(self, node):
        if self.satisfies_criteria(node):
            self._found.append(node)


class ReturnFinder(SyntaxFinder):

    """Find all return statements within given AST."""

    def __init__(self):
        super().__init__(types=(typed_ast3.Return,))

    @property
    def found_any_with_value(self) -> bool:
        return any(_.value is not None for _ in self._found)
