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
        self.assertIsNotNone(np.zeros((10, 10), dtype=int))

    @unittest.skip('not ready yet')
    def test_pyopencl(self):
        import pyopencl

    def test_gfortran(self):
        gfortran_path = shutil.which('gfortran')
        self.assertIsNotNone(gfortran_path)

    def test_swig(self):
        swig_path = shutil.which('swig')
        self.assertIsNotNone(swig_path)

    def test_typed_ast(self):
        from typed_ast import ast3
        self.assertGreaterEqual(ast3.LATEST_MINOR_VERSION, 6)
