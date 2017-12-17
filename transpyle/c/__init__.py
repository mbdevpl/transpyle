"""Support for C language."""

from ..general import Language


Language.register(Language('C99', ['.c', '.h']), ['C99'])
Language.register(Language('C11', ['.c', '.h']), ['C11', 'C'])
