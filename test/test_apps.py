"""Integration tests based on various scientific applications."""

import logging
import pathlib
import typing as t
import unittest

import timing
import typed_ast.ast3 as typed_ast3
import horast.nodes as horast_nodes

from transpyle.general import Language, Parser, AstGeneralizer, Unparser
from transpyle.pair import inline_syntax, annotate_loop_syntax

from .common import \
    APPS_RESULTS_ROOT

_LOG = logging.getLogger(__name__)

_TIME = timing.get_timing_group(__name__)


def path_selection_tree(
        *segments: t.Union[pathlib.Path, t.Dict[
            pathlib.Path, t.Union[dict, pathlib.Path]]]) -> t.List[pathlib.Path]:
    """Create list of paths based on joining and processing of path segments.

    Path segment types:
    str and pathlib.Path: selects single path
    dict: forks processing and selects each key subpath together with each value
    list: creates cartesian product of currently selected root paths with each of listed segments

    Examples:
    'a/b', ['c', 'd', 'e'] -> a/b/c a/b/d a/b/e
    'a', {'b': 'c', 'd': 'e'} -> a/b/c, a/d/e
    """
    results = []
    _LOG.debug('processing %i segments: %s', len(segments), segments)
    for segment in segments:
        _LOG.debug('current results: %s', results)
        _LOG.debug('processing segment: %s', segment)
        if not results:
            if isinstance(segment, pathlib.Path):
                results.append(segment)
            elif isinstance(segment, str):
                results.append(pathlib.Path(segment))
            else:
                raise TypeError('initial segment of type {} is not supported'.format(type(segment)))
            continue
        if isinstance(segment, pathlib.Path):
            for i, _ in enumerate(results):
                results[i] = results[i].joinpath(segment)
        elif isinstance(segment, str):
            for i, _ in enumerate(results):
                results[i] = results[i].joinpath(pathlib.Path(segment))
        elif isinstance(segment, list):
            results_ = []
            for result in results:
                for segment_item in segment:
                    results_.append(result.joinpath(segment_item))
            results = results_
        elif isinstance(segment, dict):
            partials = {}
            for key, value in segment.items():
                if isinstance(key, (pathlib.Path, str)):
                    partials[key] = path_selection_tree(key, value)
                else:
                    raise TypeError('dict segment key of type {} is not supported'
                                    .format(type(key)))
            results_ = []
            for result in results:
                for partials_ in partials.values():
                    for partial in partials_:
                        results_.append(result.joinpath(partial))
            results = results_
        else:
            raise TypeError('segment of type {} is not supported'.format(type(segment)))
    if len(results) <= 32:
        _LOG.debug('final results: %s', results)
    else:
        _LOG.debug('final results count: %i', len(results))
    return results


def _prepare_roundtrip(case, language: Language):
    parser = Parser.find(language)()
    case.assertIsInstance(parser, Parser)
    ast_generalizer = AstGeneralizer.find(language)()
    case.assertIsInstance(ast_generalizer, AstGeneralizer)
    unparser = Unparser.find(language)()
    case.assertIsInstance(unparser, Unparser)
    return parser, ast_generalizer, unparser


class AppTests(unittest.TestCase):

    app_name = None

    app_source_folder = None

    paths = []

    def _test_app(self, tools, test, dir_name=None):
        if dir_name is None:
            dir_name = self.app_name.lower()
        results_path = APPS_RESULTS_ROOT.joinpath(dir_name)
        results_path.mkdir(exist_ok=True)
        self.assertGreater(len(self.paths), 0, msg=self.app_source_folder)
        for path in self.paths:
            with self.subTest(path=path):
                test(self, path, results_path, *tools)
