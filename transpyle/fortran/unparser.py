
import typed_ast.ast3

from ..general import Language, Unparser


class FortranUnparser(Unparser):

    def __init__(self):
        super().__init__(Language.find('Fortran 2008'))

    def unparse(self, tree: typed_ast.ast3.AST) -> str:
        raise NotImplementedError()
