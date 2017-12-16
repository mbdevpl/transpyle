"""Translation of source code."""

import pathlib
import typing as t

from .language import Language
from .parser import Parser
from .ast_generalizer import AstGeneralizer
from .unparser import Unparser


class Translator:

    """Translate from one programming language to another."""

    def __init__(self, from_language: Language, to_language: Language):
        self.from_language = from_language
        self.to_language = to_language
        self.parser = Parser.find(from_language)()
        self.ast_generaliser = AstGeneralizer.find(from_language)()
        self.unparser = Unparser.find(to_language)()

    def translate(self, code: str, path: t.Optional[pathlib.Path] = None) -> str:
        # import pdb; pdb.set_trace()
        specific_ast = self.parser.parse(code, path)
        general_ast = self.ast_generaliser.generalize(specific_ast)
        to_code = self.unparser.unparse(general_ast)
        return to_code
