"""Language-specific AST generailzer."""

from .registry import Registry
from .language import Language


class AstGeneralizer(Registry):

    """Generalizer of language-specific ASTs."""

    def __init__(self, language: Language):
        self.language = language

    def generalize(self, tree):
        """Generalize a language-specific AST into a general one."""
        raise NotImplementedError()
