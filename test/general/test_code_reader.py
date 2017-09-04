"""Unit tests for CodeReader class."""

#import logging
import os
import unittest

from transpyle.general.code_reader import CodeReader

_ROOT = os.getcwd()

class Tests(unittest.TestCase):

    def setUp(self):
        super().setUp()

        self.extensions = {
            'c11': ['.c', '.h'],
            'cpp14': ['.cpp', '.hpp'],
            'cython': ['.pyx'],
            'f77': ['.f', '.F'],
            'python3': ['.py']
            }
        self.names = sorted(list(self.extensions.keys()))

    def test_construct(self):
        """ Is CodeReader constructed? """

        readers = [CodeReader(self.extensions[name]) for name in self.names]
        for name, reader in zip(self.names, readers):
            self.assertIsNotNone(reader, msg=name)
            self.assertEqual(reader.extensions, self.extensions[name], msg=reader)

    def test_read_file(self):
        """ Is file read? """

        readers = [CodeReader(self.extensions[name]) for name in self.names]
        for name, reader in zip(self.names, readers):
            dirname, _, filenames = next(
                os.walk(os.path.join(_ROOT, 'test', 'examples', name)), (None, None, []))
            file_paths = [os.path.join(dirname, filename) for filename in filenames]
            for file_path in file_paths:
                code = reader.read_file(file_path)
                self.assertGreater(len(code), 0, msg=file_path)

    def test_read_folder(self):
        """ Is folder read? """

        readers = [CodeReader(self.extensions[name]) for name in self.names]
        for name, reader in zip(self.names, readers):
            results = reader.read_folder(os.path.join(_ROOT, 'test', 'examples', name))
            self.assertGreater(len(results), 0, msg=reader)
            for path, contents in results.items():
                _, ext = os.path.splitext(path)
                self.assertIn(ext, self.extensions[name], msg=reader)
                self.assertIsNotNone(contents, msg=reader)

    def test_read_current_folder(self):
        """ Is current working directory read? """

        readers = [CodeReader(self.extensions[name]) for name in self.names]
        for name, reader in zip(self.names, readers):
            results = reader.read_folder(os.path.join('.'))
            for path, contents in results.items():
                _, ext = os.path.splitext(path)
                self.assertIn(ext, self.extensions[name], msg=reader)
                self.assertIsNotNone(contents, msg=reader)
