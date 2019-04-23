
import typing as t

import static_typing as st
import typed_ast.ast3 as typed_ast3


class LoopTransformer(st.ast_manipulation.RecursiveAstTransformer[typed_ast3]):

    pass


def annotate_loop_syntax(loop: t.Union[typed_ast3.For, typed_ast3.While],
                         annotation: typed_ast3.AST):
    return [annotation, loop]


def annotate_loops(function, annotation: str):
    raise NotImplementedError()
