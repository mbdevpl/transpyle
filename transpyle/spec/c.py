"""Support for C language."""

from .lang import Language, Languages


_C_LANG = Language(['C', 'C99', 'C11'], ['.c', '.h'])

Languages.add(_C_LANG)
