"""Unit tests for Registry class."""

import unittest

from transpyle.general.registry import Registry


class Tests(unittest.TestCase):

    def test_register_and_find(self):
        class MyRegistry(Registry):
            pass
        MyRegistry.register(42, ['the_answer', 'my answer'])
        self.assertEqual(MyRegistry.find('the_answer'), 42)
