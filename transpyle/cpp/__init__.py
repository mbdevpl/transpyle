"""Support for C++ language."""

from ..general import Language, Unparser, Compiler
from .unparser import Cpp14Unparser
from .compiler import CppSwigCompiler


# Language.register(Language('C++11', ['.cpp', '.cxx', '.h', '.hpp', '.hxx']), ['C++11'])
Language.register(Language(['C++14'], ['.cpp', '.cxx', '.h', '.hpp', '.hxx']),
                  ['C++14', 'C++', 'Cpp'])
# Language.register(Language('C++17', ['.cpp', '.cxx', '.h', '.hpp', '.hxx']), ['C++17'])

Unparser.register(Cpp14Unparser, (Language.find('C++14'),))

Compiler.register(CppSwigCompiler, (Language.find('C++14'),))
