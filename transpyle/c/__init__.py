"""Support for C language."""

from ..general import Language, Parser, AstGeneralizer
from .parser import C99Parser
from .ast_generalizer import CAstGeneralizer

Language.register(Language(['C99'], ['.c', '.h']), ['C99'])
Language.register(Language(['C11'], ['.c', '.h']), ['C11', 'C'])

Parser.register(C99Parser, (Language.find('C99'), Language.find('C11')))

AstGeneralizer.register(CAstGeneralizer, (Language.find('C99'), Language.find('C11')))
