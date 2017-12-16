"""Transpilation of source code."""

import inspect

# from .registry import Registry
from .language import Language
from .compiler import Compiler
from .binder import Binder
from .translator import Translator


class Transpiler:

    """Translate a function to another language, compile and create binding for the result."""

    def __init__(self, to_language: Language, *args, **kwargs):
        self.to_language = to_language
        self.translator = Translator(Language.find('Python 3'), to_language)
        self.compiler = Compiler(to_language, *args, **kwargs)
        self.binder = Binder.find(to_language)

    def transpile(self, function):
        from_code = inspect.getsource(function)
        to_code = self.translator.translate(from_code)
        compiled = self.compiler.compile(to_code)
        binding = self.binder.bind(compiled)
        return binding


def transpile(function, to_language: Language, *args, **kwargs):
    """Meant to be used as decorator."""
    raise NotImplementedError()
