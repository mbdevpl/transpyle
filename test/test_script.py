"""Tests for main script."""

import contextlib
import io
import unittest

from .test_setup import run_module


class Tests(unittest.TestCase):

    def test_run_bad_args(self):
        _ = io.StringIO()
        with contextlib.redirect_stderr(_):
            with self.assertRaises(SystemExit):
                run_module('transpyle')
        run_module('transpyle', 'some', 'bad', 'args', run_name='not_main')

    def test_help(self):
        sio = io.StringIO()
        with contextlib.redirect_stdout(sio):
            with self.assertRaises(SystemExit):
                run_module('transpyle', '--help')
        text = sio.getvalue()
        self.assertIn('usage', text)
        self.assertIn('transpyle', text)

    def test_help_languages(self):
        sio = io.StringIO()
        with contextlib.redirect_stdout(sio):
            run_module('transpyle', '--help-languages')
        text = sio.getvalue()
        self.assertIn('support', text)
        self.assertIn('transpyle', text)
