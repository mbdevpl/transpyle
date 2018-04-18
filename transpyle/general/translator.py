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

    def __init__(self, parser: Parser, ast_generaliser: AstGeneralizer, unparser: Unparser):
        self.parser = parser
        self.ast_generaliser = ast_generaliser
        self.unparser = unparser

    def translate(self, code: str, path: t.Optional[pathlib.Path] = None) -> str:
        specific_ast = self.parser.parse(code, path)
        general_ast = self.ast_generaliser.generalize(specific_ast)
        to_code = self.unparser.unparse(general_ast)
        return to_code

    def translate_object(self, code_object):
        assert inspect.iscode(code_object), type(code_object)
        code = inspect.getsource(code_object)
        path_str = inspect.getabsfile(code_object)
        return self.translate(code, pathlib.Path(path_str))


class AutoTranslator(Translator):

    """Automatically find parser/unparser pair and translate between programming languages."""

    def __init__(self, from_language: Language, to_language: Language):
        super().__init__(Parser.find(from_language)(), AstGeneralizer.find(from_language)(),
                         Unparser.find(to_language)())
        self.from_language = from_language
        self.to_language = to_language
