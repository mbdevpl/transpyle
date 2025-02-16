"""Test if dependencies are present in the system."""

import shutil
import unittest


class Tests(unittest.TestCase):

    def test_swig(self):
        swig_path = shutil.which('swig')
        self.assertIsNotNone(swig_path)

    def test_typed_ast(self):
        from typed_ast import ast3
        self.assertGreaterEqual(ast3.LATEST_MINOR_VERSION, 6)
