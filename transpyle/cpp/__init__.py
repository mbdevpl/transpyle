"""Support for C++ language."""

from ..general import Language, Parser, AstGeneralizer, Unparser, Compiler, Binder
from .parser import CppParser
from .ast_generalizer import CppAstGeneralizer
from .unparser import Cpp14Unparser
from .compiler import CppSwigCompiler


class CppBinder(Binder):

    pass


# Language.register(Language('C++11', ['.cpp', '.cxx', '.h', '.hpp', '.hxx']), ['C++11'])
Language.register(Language(['C++14'], ['.cpp', '.cxx', '.h', '.hpp', '.hxx']),
                  ['C++14', 'C++', 'Cpp'])
# Language.register(Language('C++17', ['.cpp', '.cxx', '.h', '.hpp', '.hxx']), ['C++17'])

Parser.register(CppParser, (Language.find('C++14'),))

AstGeneralizer.register(CppAstGeneralizer, (Language.find('C++14'),))

Unparser.register(Cpp14Unparser, (Language.find('C++14'),))

Compiler.register(CppSwigCompiler, (Language.find('C++14'),))

Binder.register(Binder, (Language.find('C++14'),))
