"""Transpilation of source code."""

import pathlib

from .registry import Registry
from .language import Language
from .compiler import Compiler
from .binder import Binder
from .translator import Translator, AutoTranslator


class Transpiler(Registry):

    """Translate a function to another language, compile and create binding for the result."""

    def __init__(self, translator: Translator, compiler: Compiler, binder: Binder):
        self.translator = translator
        self.compiler = compiler
        self.binder = binder

    def transpile(self, code: str, path: pathlib.Path = None):
        """Transpile given"""
        translated_code = self.translator.translate(code, path)
        compiled = self.compiler.compile(translated_code)
        binding = self.binder.bind(compiled)
        return binding


class AutoTranspiler(Transpiler):

    """Translate a function to another language, compile and create binding for the result."""

    def __init__(self, from_language: Language, to_language: Language):
        super().__init__(AutoTranslator(from_language, to_language),
                         Compiler.find(to_language)(),
                         Binder.find(to_language)())
        self.to_language = to_language
