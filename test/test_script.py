"""Tests for main script."""

import contextlib
import io
import unittest

from .test_setup import run_module


class Tests(unittest.TestCase):

    def test_run_not_main(self):
        run_module('transpyle', 'some', 'bad', 'args', run_name='not_main')

    def test_help(self):
        sio = io.StringIO()
        with contextlib.redirect_stderr(sio):
            with self.assertRaises(SystemExit):
                run_module('transpyle')
        text = sio.getvalue()
        self.assertIn('usage', text)
        self.assertIn('transpyle', text)
