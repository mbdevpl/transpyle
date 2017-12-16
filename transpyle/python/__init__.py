"""Python support for transpyle package."""

import inspect

from ..general import Language, Parser, AstGeneralizer, Unparser
from .parser import TypedPythonParserWithComments
from .ast_generalizer import PythonAstGeneralizer
from .unparser import TypedPythonUnparserWithComments


Language.register(Language(['Python 3.5'], ['.py']), ['Python 3.5'])
Language.register(Language(['Python 3.6'], ['.py']), ['Python 3.6', 'Python 3', 'Python'])

Parser.register(TypedPythonParserWithComments,
                (Language.find('Python 3.5'), Language.find('Python 3.6')))

AstGeneralizer.register(PythonAstGeneralizer,
                        (Language.find('Python 3.5'), Language.find('Python 3.6')))

Unparser.register(TypedPythonUnparserWithComments,
                  (Language.find('Python 3.5'), Language.find('Python 3.6')))
