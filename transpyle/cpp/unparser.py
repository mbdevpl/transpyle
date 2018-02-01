"""Unparse into C++."""

import io
import horast
import nuitka

from ..general import Language, Unparser


def transpile_test():
    command = ['nuitka', '--module', '{}.py']
    raise NotImplementedError()


class Cpp14UnparserBackend(horast.unparser.Unparser):

    """Implementation of C++14 unparser."""

    def _ClassDef(self, t):
        raise NotImplementedError('not supported yet')

    def _FunctionDef(self, t):
        raise NotImplementedError('not supported yet')

    def _Comment(self, node):
        if node.eol:
            self.write('  //')
        else:
            self.fill('//')
        self.write(node.value.s)


class Cpp14HeaderUnparserBackend(Cpp14UnparserBackend):

    def _FunctionDef(self, t):
        raise NotImplementedError()


class Cpp14Unparser(Unparser):

    def __init__(self, headers: bool = False):
        super().__init__(Language.find('C++14'))
        self.headers = headers

    def unparse(self, tree) -> str:
        stream = io.StringIO()
        backend = Cpp14HeaderUnparserBackend if self.headers else Cpp14UnparserBackend
        backend(tree, file=stream)
        return stream.getvalue()
