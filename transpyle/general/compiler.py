"""Language-specific compiler interfaces."""

import pathlib
import typing as t

from .registry import Registry
from .code_reader import CodeReader


class Compiler(Registry):

    """Interface for language-specific compilers."""

    _reader = None

    def __init__(self, *args, **kwargs):
        self.default_args = args
        self.default_kwargs = kwargs

    def compile(self, code: str, path: t.Optional[pathlib.Path] = None,
                output_folder: t.Optional[pathlib.Path] = None, **kwargs) -> pathlib.Path:
        raise NotImplementedError()

    def compile_file(self, path: pathlib.Path, output_folder=None):
        if self._reader is None:
            self._reader = CodeReader()
        code = self._reader.read_file(path)
        return self.compile(code, path, output_folder)
