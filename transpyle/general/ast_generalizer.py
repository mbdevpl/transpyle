"""Language-specific AST generailzer."""

from .registry import Registry
from .language import Language


class AstGeneralizer(Registry):

    def __init__(self, language: Language):
        self.language = language
