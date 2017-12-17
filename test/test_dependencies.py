"""Test if dependencies are present in the system."""

import shutil
import unittest

class Tests(unittest.TestCase):

    def test_cython(self):
        import cython

    def test_nuitka(self):
        import nuitka

    def test_numpy(self):
        import numpy as np

    @unittest.skip('not ready yet')
    def test_pyopencl(self):
        import pyopencl

    def test_swig(self):
        shutil.which('swig')

    def test_typed_ast(self):
        from typed_ast import ast3
        assert ast3.LATEST_MINOR_VERSION >= 6, ast3.LATEST_MINOR_VERSION
