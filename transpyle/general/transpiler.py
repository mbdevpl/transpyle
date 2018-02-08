"""Transpilation of source code."""

import pathlib

from .registry import Registry
from .code_writer import CodeWriter
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

    def transpile(self, code: str, path: pathlib.Path = None, translated_path: pathlib.Path = None,
                  compile_folder: pathlib.Path = None):
        """Transpile given"""
        translated_code = self.translator.translate(code, path)
        code_writer = CodeWriter(translated_path.suffix)
        code_writer.write_file(translated_code, translated_path)
        compiled_path = self.compiler.compile(translated_code, translated_path, compile_folder)
        binding = self.binder.bind(compiled_path)
        return binding


class AutoTranspiler(Transpiler):

    """Translate a function to another language, compile and create binding for the result."""

    def __init__(self, from_language: Language, to_language: Language):
        super().__init__(AutoTranslator(from_language, to_language),
                         Compiler.find(to_language)(),
                         Binder.find(to_language)())
        self.to_language = to_language
