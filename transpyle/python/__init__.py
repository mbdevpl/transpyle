"""Python support for transpyle package."""

import inspect

from ..general import \
    Language, Parser, AstGeneralizer, IdentityAstGeneralizer, Unparser, Translator, AutoTranspiler
from .parser import TypedPythonParserWithComments
from .unparser import TypedPythonUnparserWithComments
from .translator import PythonTranslator


Language.register(Language(['Python 3.5'], ['.py']), ['Python 3.5'])
Language.register(Language(['Python 3.6'], ['.py']), ['Python 3.6', 'Python 3', 'Python'])

Parser.register(TypedPythonParserWithComments,
                (Language.find('Python 3.5'), Language.find('Python 3.6')))


class PythonAstGeneralizer(IdentityAstGeneralizer):

    """Python doesn't need AST generalizer."""

    def __init__(self):
        super().__init__(Language.find('Python 3'))


AstGeneralizer.register(PythonAstGeneralizer,
                        (Language.find('Python 3.5'), Language.find('Python 3.6')))

Unparser.register(TypedPythonUnparserWithComments,
                  (Language.find('Python 3.5'), Language.find('Python 3.6')))

Translator.register(PythonTranslator, (Language.find('Python 3.5'), Language.find('Python 3.6')))


def transpile(function_or_class, to_language: Language, *args, **kwargs):
    """Instantiate Python transpiler to transpile one function or class.

    Meant to be used as decorator."""
    transpiler = AutoTranspiler(Language.find('Python 3'), to_language)
    return transpiler.transpile(function_or_class)
