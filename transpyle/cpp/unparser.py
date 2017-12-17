"""Unparse into C++."""

import nuitka
import horast

from ..general import Unparser


def transpile():
    command = ['nuitka', '--module', '{}.py']


class Cpp14UnparserBackend(horast.unparser.Unparser):

    pass


class Cpp14Unparser(Unparser):

    pass
