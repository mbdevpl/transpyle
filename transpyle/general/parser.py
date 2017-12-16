"""Definition of parser"""

import pathlib

from .registry import Registry
from .language import Language


class Parser(Registry):

    def __init__(self, language: Language):
        self.language = language

    def parse(self, code: str, path: pathlib.Path = None):
        """Parse given code into a language-specific AST.

        If path is provided, use it to guide the parser if necessary.
        """
        raise NotImplementedError()
