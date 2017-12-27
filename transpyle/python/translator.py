"""Translating Python."""

import inspect
import pathlib

from ..general import Language, AutoTranslator


class PythonTranslator(AutoTranslator):

    def __init__(self, to_language: Language):
        super().__init__(Language.find('Python 3'), to_language)
