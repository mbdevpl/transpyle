"""Tests for Binder class."""

import logging
import pathlib
import sys
import unittest

from transpyle.general.binder import Binder

from test.common import EXAMPLES_ROOTS

_LOG = logging.getLogger(__name__)


class Tests(unittest.TestCase):

    def test_construct(self):
        binder = Binder()
        self.assertIsNotNone(binder)

    def test_bind_module(self):
        binder = Binder()
        binding = binder.bind_module('unittest')
        self.assertIsNotNone(binding)
        binding = binder.bind_module('numpy')
        self.assertIsNotNone(binding)

    def test_bind_object(self):
        binder = Binder()
        binding = binder.bind_object('unittest', 'TestCase')
        self.assertIs(binding, unittest.TestCase)

        path = pathlib.Path(__file__)
        binding = binder.bind_object(path, 'Binder')
        self.assertIs(binding, Binder)
        del sys.modules[path.with_suffix('').name]

        with self.assertRaises(TypeError):
            binder.bind_object(3, 1415)

    def test_bind_object_default(self):
        binder = Binder()
        with self.assertRaises(ValueError):
            binder.bind_object(pathlib.Path(__file__))

        binding = binder.bind_object(EXAMPLES_ROOTS['python3'].joinpath('matmul.py'))
        self.assertIsInstance(binding, object)
        del sys.modules['matmul']

    def test_bind(self):
        binder = Binder()
        path = pathlib.Path(__file__)
        binding = binder.bind(path)
        self.assertIsNotNone(binding)
        del sys.modules[path.with_suffix('').name]

        with self.assertRaises(ValueError):
            binder.bind(EXAMPLES_ROOTS['f77'].joinpath('matmul.f'))
