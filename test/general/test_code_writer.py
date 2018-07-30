"""Unit tests for CodeWriter class."""

import pathlib
import unittest

from transpyle.general.code_writer import CodeWriter

from test.common import EXAMPLES_EXTENSIONS


class Tests(unittest.TestCase):

    def test_construct(self):
        for name, extensions in EXAMPLES_EXTENSIONS.items():
            for extension in extensions:
                with self.subTest(name=name, extension=extension):
                    writer = CodeWriter(extension)
                    self.assertIsNotNone(writer)
                    self.assertEqual(writer.extension, extension)

    def test_write(self):
        for name, extensions in EXAMPLES_EXTENSIONS.items():
            for extension in extensions:
                with self.subTest(name=name, extension=extension):
                    writer = CodeWriter(extension)

                    path = pathlib.Path('/tmp', 'example' + extension)
                    writer.write_file('blah', path)

                    bad_path = pathlib.Path('/tmp', 'example' + '.txt')
                    with self.assertRaises(ValueError):
                        writer.write_file('blah', bad_path)

                    created_path = writer.write_module('blah', '/tmp/example')
                    self.assertEqual(path, created_path)
