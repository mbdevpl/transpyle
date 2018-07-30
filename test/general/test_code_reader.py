"""Unit tests for CodeReader class."""

import itertools
import pathlib
import unittest

from transpyle.general.code_reader import CodeReader

from test.common import _HERE, EXAMPLES_EXTENSIONS, EXAMPLES_ROOTS, EXAMPLES_FILES


class Tests(unittest.TestCase):

    def test_construct_default(self):
        reader = CodeReader()
        self.assertIsNotNone(reader)
        self.assertSetEqual(reader.extensions, set(), msg=reader)
        self.assertIn(str(set()), str(reader))

    def test_construct(self):
        for name, extensions in EXAMPLES_EXTENSIONS.items():
            with self.subTest(name=name, extensions=extensions):
                reader = CodeReader(extensions)
                self.assertSetEqual(reader.extensions, set(extensions), msg=reader)
                self.assertIn(str(set(extensions)), str(reader))

    def test_read_file(self):
        for name, extensions in EXAMPLES_EXTENSIONS.items():
            with self.subTest(name=name, extensions=extensions):
                reader = CodeReader(extensions)
                for file_path in EXAMPLES_FILES[name]:
                    code = reader.read_file(file_path)
                    self.assertGreater(len(code), 0, msg=file_path)

    def test_read_folder(self):
        for (name, extensions), recursive in itertools.product(
                EXAMPLES_EXTENSIONS.items(), (False, True)):
            with self.subTest(name=name, extensions=extensions):
                reader = CodeReader(extensions)
                results = reader.read_folder(EXAMPLES_ROOTS[name], recursive=recursive)
                self.assertGreater(len(results), 0, msg=EXAMPLES_ROOTS[name])
                for path, contents in results.items():
                    self.assertIn(path.suffix, extensions)
                    self.assertIsNotNone(contents)

    def test_read_project_folder(self):
        for name, extensions in EXAMPLES_EXTENSIONS.items():
            with self.subTest(name=name, extensions=extensions):
                reader = CodeReader(extensions)
                results = reader.read_folder(_HERE.parent)
                self.assertGreater(len(results), 0, msg=EXAMPLES_ROOTS[name])
                for path, contents in results.items():
                    self.assertIn(path.suffix, extensions)
                    self.assertIsNotNone(contents)

    def test_read_function(self):
        def my_function_example():
            pass
        code = CodeReader.read_function(my_function_example)
        self.assertIn('def my_function_example()', code)
        self.assertIn('pass', code)

    def test_errors(self):
        reader = CodeReader({'.py'})
        with self.assertRaises(OSError):
            reader.read_file(pathlib.Path(EXAMPLES_ROOTS['python3'], 'non-existing', 'script.py'))
        with self.assertRaises(ValueError):
            reader.read_file(pathlib.Path(EXAMPLES_FILES['cpp14'][0]))
        with self.assertRaises(OSError):
            reader.read_folder(pathlib.Path(EXAMPLES_ROOTS['python3'], 'non-existing'))
