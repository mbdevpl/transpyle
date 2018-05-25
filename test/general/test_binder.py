"""Tests for Binder class."""

import pathlib
import unittest

from transpyle.general.binder import Binder


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

        binding = binder.bind_object(pathlib.Path(__file__), 'Binder')
        self.assertIs(binding, Binder)

        with self.assertRaises(TypeError):
            binder.bind_object(3, 1415)

    def test_bind_object_default(self):
        binder = Binder()
        with self.assertRaises(ValueError):
            binder.bind_object(pathlib.Path(__file__))

        binding = binder.bind_object(pathlib.Path(__file__,).parent
                                     .joinpath('..', 'examples', 'python3', 'matmul.py'))
        self.assertIsInstance(binding, object)

    def test_bind(self):
        binder = Binder()
        binding = binder.bind(pathlib.Path(__file__))
        self.assertIsNotNone(binding)

        with self.assertRaises(ImportError):
            binder.bind(pathlib.Path(__file__).parent.joinpath('..', 'examples', 'f77', 'matmul.f'))
