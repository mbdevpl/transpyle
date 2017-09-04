"""Support for C++ language."""

import typed_ast.ast3
import typed_astunparse.unparser

from .lang import Language, Languages


_CPP = Language(['C++', 'Cpp'], ['.cpp', '.cxx', '.h', 'hpp', '.hxx'])

Languages.add(_CPP)


def transpile():

    command = ['nuitka', '--module', '{}.py']


def unparse(tree: typed_ast.ast3):
    
    pass


class Cpp14Unparser(typed_astunparse.unparser.Unparser):

    pass
