"""Automatic parsing and generailzation of language-specific ASTs."""

import pathlib
import typing as t

import typed_ast.ast3 as typed_ast3

from .language import Language
from .parser import Parser
from .ast_generalizer import AstGeneralizer


class GeneralizingAutoParser:

    """Automatically find parser and generalizer set to obtain PAIR from code."""

    def __init__(
            self, language: Language, parser_kwargs: dict = {}, ast_generalizer_kwargs: dict = {}):
        super().__init__()
        self.language = language
        self.parser = Parser.find(language)(**parser_kwargs)
        self.ast_generalizer = AstGeneralizer.find(language)(**ast_generalizer_kwargs)

    def parse_and_generalize(
            self, code: str, path: pathlib.Path = None,
            scopes: t.Sequence[t.Tuple[int, t.Optional[int]]] = None,
            dedent: bool = True) -> typed_ast3:
        """Parse the given code, and then generalize it using Python as IR."""
        syntax = self.parser.parse(code, path, scopes, dedent)
        return self.ast_generalizer.generalize(syntax)

    def parse_and_generalize_file(self, path: pathlib.Path) -> typed_ast3:
        """Read a given file, parse it, and then generalize the syntax using Python as IR."""
        syntax = self.parser.parse_file(path)
        return self.ast_generalizer.generalize(syntax)
