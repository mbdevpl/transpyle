"""Translation of source code."""

import inspect
import pathlib
import typing as t

from .registry import Registry
from .language import Language
from .parser import Parser
from .ast_generalizer import AstGeneralizer
from .unparser import Unparser


class Translator(Registry):

    """Translate from one programming language to another."""

    def __init__(self, parser: Parser, ast_generalizer: AstGeneralizer, unparser: Unparser):
        self.parser = parser
        self.ast_generalizer = ast_generalizer
        self.unparser = unparser

    def translate(self, code: str, path: t.Optional[pathlib.Path] = None, parser_kwargs: dict = {},
                  ast_generalizer_kwargs: dict = {}, unparser_kwargs: dict = {}) -> str:
        specific_ast = self.parser.parse(code, path, **parser_kwargs)
        general_ast = self.ast_generalizer.generalize(specific_ast, **ast_generalizer_kwargs)
        to_code = self.unparser.unparse(general_ast, **unparser_kwargs)
        return to_code

    def translate_object(self, code_object) -> str:
        assert inspect.iscode(code_object), type(code_object)
        code = inspect.getsource(code_object)
        path_str = inspect.getabsfile(code_object)
        return self.translate(code, pathlib.Path(path_str))


class AutoTranslator(Translator):

    """Automatically find parser/unparser pair and translate between programming languages."""

    def __init__(self, from_language: Language, to_language: Language, parser_kwargs: dict = {},
                 ast_generalizer_kwargs: dict = {}, unparser_kwargs: dict = {}):
        super().__init__(Parser.find(from_language)(**parser_kwargs),
                         AstGeneralizer.find(from_language)(**ast_generalizer_kwargs),
                         Unparser.find(to_language)(**unparser_kwargs))
        self.from_language = from_language
        self.to_language = to_language
