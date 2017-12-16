"""Unparsing of general AST into code in given language."""

# import logging
# import typing as t

from .registry import Registry
from .language import Language


class Unparser(Registry):

    """Output code in a given language."""

    def __init__(self, language: Language):
        self.language = language

    def unparse(self, tree) -> str:
        raise NotImplementedError()
