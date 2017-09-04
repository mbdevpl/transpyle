"""Translation of source code."""

import pathlib
import typing as t


class Translator:

    def __init__(self, from_language, to_language, *args, **kwargs):
        raise NotImplementedError()

    def translate(self, code: str, *args, **kwargs) -> t.Union[str, pathlib.Path]:
        raise NotImplementedError()
