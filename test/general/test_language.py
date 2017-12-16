"""Unit tests for Language class."""

import unittest

from transpyle.general.language import Language


class Tests(unittest.TestCase):

    def test_assert_languages(self):
        self.assertIn('Python', Language.registered)
