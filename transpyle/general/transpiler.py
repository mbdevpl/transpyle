"""Transpilation of source code."""

import pathlib
import tempfile

from .registry import Registry
from .code_reader import CodeReader
from .code_writer import CodeWriter
from .language import Language
from .compiler import Compiler
from .translator import Translator, AutoTranslator


class Transpiler(Registry):

    """Translate a function to another language, compile and create binding for the result."""

    _reader = None

    def __init__(self, translator: Translator, compiler: Compiler):
        self.translator = translator
        self.compiler = compiler

    def transpile(self, code: str, path: pathlib.Path = None, translated_path: pathlib.Path = None,
                  compile_folder: pathlib.Path = None) -> pathlib.Path:
        """Transpile given code."""
        assert isinstance(path, pathlib.Path), type(path)
        assert path.is_file(), path
        assert isinstance(translated_path, pathlib.Path), type(translated_path)
        assert isinstance(compile_folder, pathlib.Path), type(compile_folder)
        assert compile_folder.is_dir(), compile_folder
        translated_code = self.translator.translate(code, path)
        code_writer = CodeWriter(translated_path.suffix)
        code_writer.write_file(translated_code, translated_path)
        compiled_path = self.compiler.compile(translated_code, translated_path, compile_folder)
        return compiled_path

    def transpile_file(self, path: pathlib.Path):
        if self._reader is None:
            self._reader = CodeReader()
        code = self._reader.read_file(path)

        translated_path = None
        with tempfile.NamedTemporaryFile(
                suffix=self.translator.to_language.default_file_extension) as translated_file:
            # TODO: this leaves garbage behind in /tmp/ but is neeeded by some transpiler passes
            translated_path = pathlib.Path(translated_file.name)

        compile_folder = None
        with tempfile.TemporaryDirectory() as compile_dir_name:
            compile_folder = pathlib.Path(compile_dir_name)
        if not compile_folder.is_dir():
            compile_folder.mkdir()

        return self.transpile(code, path, translated_path, compile_folder)


class AutoTranspiler(Transpiler):

    """Translate a function to another language, compile and create binding for the result."""

    def __init__(self, from_language: Language, to_language: Language):
        super().__init__(AutoTranslator(from_language, to_language), Compiler.find(to_language)())
        self.from_language = from_language
        self.to_language = to_language
