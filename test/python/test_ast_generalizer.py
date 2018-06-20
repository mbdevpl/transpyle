"""Tests for Python language generalization (not much to test)."""

import unittest

import typed_ast.ast3


class Tests(unittest.TestCase):

    def test_ast_generalizer(self):
        tree = typed_ast.ast3.parse("""my_file: t.IO[bytes] = None""", mode='exec')
        self.assertIsInstance(tree, typed_ast.ast3.Module)
        self.assertIsInstance(tree.body[0], typed_ast.ast3.AnnAssign)
        self.assertIsInstance(tree.body[0].annotation, typed_ast.ast3.Subscript)

        tree = typed_ast.ast3.parse("""my_mapping: t.Dict[int, str] = {}""", mode='exec')
        self.assertIsInstance(tree, typed_ast.ast3.Module)
        self.assertIsInstance(tree.body[0], typed_ast.ast3.AnnAssign)
        self.assertIsInstance(tree.body[0].annotation, typed_ast.ast3.Subscript)
        self.assertIsInstance(tree.body[0].annotation.slice, typed_ast.ast3.Index)

        tree = typed_ast.ast3.parse("""my_mapping: t.Dict[1:2, str] = {}""", mode='exec')
        self.assertIsInstance(tree, typed_ast.ast3.Module)
        self.assertIsInstance(tree.body[0], typed_ast.ast3.AnnAssign)
        self.assertIsInstance(tree.body[0].annotation, typed_ast.ast3.Subscript)
        self.assertIsInstance(tree.body[0].annotation.slice, typed_ast.ast3.ExtSlice)
