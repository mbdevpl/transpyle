"""Unit tests for CodeReader class."""

import pathlib
import unittest

from transpyle.general.code_reader import CodeReader
from ..examples import EXAMPLES_EXTENSIONS, EXAMPLES_ROOTS, EXAMPLES_FILES


class Tests(unittest.TestCase):

    def test_construct(self):
        for name, extensions in EXAMPLES_EXTENSIONS.items():
            with self.subTest(name=name, extensions=extensions):
                reader = CodeReader(extensions)
                self.assertIsNotNone(reader, msg=name)
                self.assertListEqual(reader.extensions, extensions, msg=reader)

    def test_read_file(self):
        for name, extensions in EXAMPLES_EXTENSIONS.items():
            with self.subTest(name=name, extensions=extensions):
                reader = CodeReader(extensions)
                for file_path in EXAMPLES_FILES[name]:
                    code = reader.read_file(file_path)
                    self.assertGreater(len(code), 0, msg=file_path)

    def test_read_folder(self):
        for name, extensions in EXAMPLES_EXTENSIONS.items():
            with self.subTest(name=name, extensions=extensions):
                reader = CodeReader(extensions)
                results = reader.read_folder(EXAMPLES_ROOTS[name])
                self.assertGreater(len(results), 0, msg=EXAMPLES_ROOTS[name])
                for path, contents in results.items():
                    self.assertIn(path.suffix, extensions)
                    self.assertIsNotNone(contents)

    def test_read_current_folder(self):
        for name, extensions in EXAMPLES_EXTENSIONS.items():
            with self.subTest(name=name, extensions=extensions):
                reader = CodeReader(extensions)
                results = reader.read_folder(pathlib.Path('.'))
                self.assertGreater(len(results), 0, msg=EXAMPLES_ROOTS[name])
                for path, contents in results.items():
                    self.assertIn(path.suffix, extensions)
                    self.assertIsNotNone(contents)
