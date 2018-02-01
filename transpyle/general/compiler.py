"""Language-specific compiler interfaces."""

import pathlib
import typing as t

from .registry import Registry


class Compiler(Registry):

    """Interface for language-specific compilers."""

    def __init__(self, *args, **kwargs):
        self.default_args = args
        self.default_kwargs = kwargs

    def compile(self, code: str, path: t.Optional[pathlib.Path] = None,
                output_folder: t.Optional[pathlib.Path] = None, *args, **kwargs) -> pathlib.Path:
        raise NotImplementedError()
