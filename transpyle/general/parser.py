"""Definition of parser."""

import collections.abc
import pathlib
import re
import textwrap
import typing as t

from .registry import Registry


# def remove_trailing_whitespace(code: str) -> str:
#    raise NotImplementedError()


def validate_indentation(code: str, path: pathlib.Path = None):
    """Raise error if code isn't consistently indented (either only with spaces, or only with tabs).

    Path is optional and used only for diagnostic purposes (i.e. if error happens).
    """
    if not isinstance(code, str):
        raise TypeError('code must be string but {} given'.format(type(code)))
    assert path is None or isinstance(path, pathlib.Path), type(path)

    lines = code.splitlines(keepends=True)
    whitespace = r'[ \t]*'
    mixed_indent = r'( {0}\t{0})|(\t{0} {0})'.format(whitespace)
    indent_by_spaces = r'[ ]+'
    indent_by_tabs = r'[\t]+'
    indented_with_spaces = None  # type: t.Optional[bool]
    for i, line in enumerate(lines):
        # check if indentation is not mixed
        if re.match(mixed_indent, line) is not None:
            raise ValueError('{}:{} mixed indentation found in {}'.format(
                '<string>' if path is None else path, i, repr(line)))

        # check if indentation type is consistent
        if indented_with_spaces is None:
            if re.match(indent_by_spaces, line) is not None:
                indented_with_spaces = True
            elif re.match(indent_by_tabs, line) is not None:
                indented_with_spaces = False
        elif indented_with_spaces:
            if re.match(indent_by_tabs, line) is not None:
                raise ValueError(
                    '{}:{} after space indent in previous lines, tab indent found in {}'
                    .format('<string>' if path is None else path, i, repr(line)))
        else:
            if re.match(indent_by_spaces, line) is not None:
                raise ValueError(
                    '{}:{} after tab indent in previous lines, space indent found in {}'
                    .format('<string>' if path is None else path, i, repr(line)))


class Parser(Registry):

    """Extract abstract representation of syntax from the source code."""

    def __init__(self, default_scopes: t.Sequence[t.Tuple[int, t.Optional[int]]] = None):
        """Initialize new Parser instance.

        Default scopes, if provided, limit parsing to the given line sections unless the default
        is overriden.
        """
        if default_scopes is None:
            default_scopes = [(0, None)]
        self.default_scopes = default_scopes

    def parse(self, code: str, path: pathlib.Path = None,
              scopes: t.Sequence[t.Tuple[int, t.Optional[int]]] = None, dedent: bool = True):
        """Parse given code into a language-specific AST.

        If path is provided, use it to guide the parser if necessary, as well as for diagnostics.
        """
        assert isinstance(code, str), type(code)
        assert path is None or isinstance(path, pathlib.Path), type(path)
        assert scopes is None or isinstance(scopes, collections.abc.Sequence), type(scopes)

        if scopes is None:
            scopes = self.default_scopes
        parsed_scopes = []
        for begin, end in scopes:
            assert isinstance(begin, int), type(begin)
            assert end is None or isinstance(end, int), type(end)
            if begin == 0 and end is None:
                code_scope = code
            else:
                lines = code.splitlines(keepends=True)
                if end is None:
                    end = len(lines)
                code_scope = ''.join(lines[begin:end])
            validate_indentation(code_scope, path)
            if dedent:
                code_scope = textwrap.dedent(code_scope)
            parsed_scope = self._parse_scope(code_scope, path)
            parsed_scopes.append(parsed_scope)
        if len(scopes) == 1:
            return parsed_scopes[0]
        return self._join_scopes(parsed_scopes)

    def _parse_scope(self, code: str, path: pathlib.Path = None):
        raise NotImplementedError('{} is abstract'.format(type(self).__name__))

    def _join_scopes(self, parsed_scopes):
        raise NotImplementedError('{} cannot join multiple parsed scopes'
                                  .format(type(self).__name__))
