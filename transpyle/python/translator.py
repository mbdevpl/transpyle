"""Translate Python to any supported language."""

import inspect
import pathlib

from ..general import Language, AutoTranslator


class PythonTranslator(AutoTranslator):

    def __init__(self, to_language: Language):
        super().__init__(Language.find('Python 3'), to_language)

    def translate(self, code_or_code_object, path: pathlib.Path = None):
        if isinstance(code_or_code_object, str):
            code = code_or_code_object
        elif isinstance(code_or_code_object, code_object):
            code = inspect.getsource(code_or_code_object)
            if path is None:
                path = inspect.getpath(code_or_code_object)
        else:
            raise TypeError(type(code_or_code_object))
        return self.translate(code, path)
