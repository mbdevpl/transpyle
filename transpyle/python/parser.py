"""Parsing Python."""

import ast
import logging
import pathlib
import re
import traceback
import typing as t

import horast
import static_typing as st
import typed_ast.ast3 as typed_ast3

from ..general import Language, Parser

_LOG = logging.getLogger(__name__)

PARSER_MODES = ('exec', 'eval', 'single')

PARSER_MODES_SET = set(PARSER_MODES)


def infer_parser_mode(code: str, excluded_modes: t.Set[str]) -> str:
    """Infer the correct parer mode based on code properties and previous parse attempts."""
    assert isinstance(code, str)

    if len(code.splitlines()) == 1:
        if len(code) <= 16:
            if 'eval' not in excluded_modes:
                return 'eval'
        if 'single' not in excluded_modes:
            return 'single'
    for mode in PARSER_MODES:
        if mode not in excluded_modes:
            return mode
    raise RuntimeError('all possible parser modes have been excluded')


class NativePythonParser(Parser):

    """Python 3 two-in-one lexer and parser based on a built-in Python modules.

    Built-in function compile() with flag ast.PyCF_ONLY_AST is used to perform AST creation.
    """

    def __init__(self, default_scopes=None, default_mode: str = None):
        super().__init__(default_scopes)

        assert default_mode is None or \
            isinstance(default_mode, str) and default_mode in PARSER_MODES_SET

        self.default_mode = default_mode
        # with ast.parse() optimization cannot be set explicitly
        self.parse_function = compile
        self.parse_function_kwargs = {'flags': ast.PyCF_ONLY_AST, 'dont_inherit': True,
                                      'optimize': 0}

    def _parse_scope(self, code, path: pathlib.Path = None) -> ast.AST:
        filename = '<string>' if path is None else str(path)
        if self.default_mode is not None:
            self._parse_scope_in_mode(code, filename, self.default_mode)

        parse_errors = {}  # type: t.Dict[str, SyntaxError]
        while any((mode not in parse_errors) for mode in PARSER_MODES_SET):
            mode = infer_parser_mode(code, parse_errors)
            try:
                return self._parse_scope_in_mode(code, filename, mode)
            except SyntaxError as err:
                parse_errors[mode] = err
                _LOG.debug('%s failed in mode %s', type(self).__name__, mode, exc_info=1)

        raise SyntaxError('all possible parser modes have been excluded:\n\n{}'.format('\n\n'.join([
            '*** {} ***\n\n{}'.format(mode, ''.join(traceback.format_exception(
                type(error), error, None)))
            for mode, error in parse_errors.items()])))

    def _parse_scope_in_mode(self, code: str, filename: str, mode: str):
        try:
            return self.parse_function(code, filename=filename, mode=mode,
                                       **self.parse_function_kwargs)
        except SyntaxError as err:
            raise SyntaxError('{} failed in mode="{}"'
                              .format(self.parse_function.__name__, mode)) from err


class TypedPythonParser(NativePythonParser):

    """Rely on typed_ast package to parse Python."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parse_function = typed_ast3.parse
        self.parse_function_kwargs = {}


class TypedPythonParserWithComments(TypedPythonParser):

    """Rely on horast and static_typing packages to parse Python into AST."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parse_function = horast.parse
        self.resolver = st.ast_manipulation.TypeHintResolver[typed_ast3, typed_ast3](eval_=False)
        self.typer = st.static_typer.StaticTyper[typed_ast3]()

    def _parse_scope_in_mode(self, code: str, filename: str, mode: str):
        syntax = super()._parse_scope_in_mode(code, filename, mode)
        syntax = self.resolver.visit(syntax)
        syntax = self.typer.visit(syntax)
        return syntax
