'''
Created on 11 May 2016

@author: mb
'''

import ast
#import inspect
import logging
import re
import typing as t

import horast
import typed_ast.ast3
#import static_typing as st

from ..general import Language, Parser


_LOG = logging.getLogger(__name__)

_UNIQUE_DELIMITER = '/////'
COMMENT_PREFIX = ' comment: '
COMMENT_FULL_PREFIX = _UNIQUE_DELIMITER + COMMENT_PREFIX
COMMENT_SUFFIX = _UNIQUE_DELIMITER
DIRECTIVE_PREFIX = ' pragma: '
DIRECTIVE_FULL_PREFIX = _UNIQUE_DELIMITER + DIRECTIVE_PREFIX
DIRECTIVE_SUFFIX = _UNIQUE_DELIMITER

_PATTERN_WHITESPACE = re.compile(r'[ \t]*')
_PATTERN_INDENT = re.compile(r'[ ]+')

_RAW_COMMENT_PREFIX = '"""' + COMMENT_FULL_PREFIX
_RAW_COMMENT_SUFFIX = COMMENT_SUFFIX + '"""'
_RAW_DIRECTIVE_PREFIX = '"""' + DIRECTIVE_FULL_PREFIX
_RAW_DIRECTIVE_SUFFIX = DIRECTIVE_SUFFIX + '"""'

PARSER_MODES = ('exec', 'eval', 'single')

PARSER_MODES_SET = set(PARSER_MODES)


def preprocess_python_code(
        code: str, remove_indent: bool = True, mangle_comments: bool = False) -> str:
    """Preprocess Python code to prevent loss of information in parsing and/or fix parse errors.

    Specifically:

    - transform directive comments and all other comments except type comments
      to specially formatted string literals,

    - remove excess indentation.
    """
    assert isinstance(code, str)

    lines = code.splitlines()

    if not lines:
        return code

    min_indent = None
    for i, line in enumerate(lines):
        if len(line) == 0:
            continue

        if remove_indent:
            # get indent towards calculating mininmum indent of code
            match = _PATTERN_INDENT.match(line)
            if match is None:
                if _PATTERN_WHITESPACE.fullmatch(line) is not None:
                    continue
                min_indent = 0
                break
            _, end = match.span()
            if min_indent is None or end < min_indent:
                min_indent = end

        if mangle_comments:
            if re.fullmatch(r"\s*#!.*'", line):
                lines[i] = line[:-1].replace("#!", _RAW_DIRECTIVE_PREFIX, 1) + _RAW_DIRECTIVE_SUFFIX
            elif re.fullmatch(r"\s*# type:.*'", line):
                continue
            elif re.fullmatch(r"\s*#.*'", line):
                lines[i] = line[:-1].replace("#", _RAW_COMMENT_PREFIX, 1) + _RAW_COMMENT_SUFFIX

    if min_indent is None:
        min_indent = 0

    code = '\n'.join([line[min_indent:] for line in lines])

    return code


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


def postprocess_typed_ast(tree) -> int:
    """Postprocess the typed AST in-place.

    Parse all type hints stored as string literals, i.e. all string literals that represent:

     - type annotations, and
     - type comments

    are parsed and resulting ASTs replace the string literals.

    Return total number of changes performed.
    """
    #comment_transformer = TypeCommentTransformer[typed_ast.ast3, ast](
    #    globals_=globals_, locals_=locals_)
    #comment_tree = comment_transformer.visit(tree)
    #_LOG.debug('%s', typed_ast.ast3.dump(comment_tree))

    #annotation_transformer = TypeAnnotationTransformer[typed_ast.ast3, ast](
    #    globals_=globals_, locals_=locals_)
    #annotation_tree = annotation_transformer.visit(comment_tree)
    #_LOG.debug('%s', typed_ast.ast3.dump(annotation_tree))

    #return annotation_tree

    changes = 0
    for node in typed_ast.ast3.walk(tree):
        # parse type annotations stored as Str nodes
        if hasattr(node, 'annotation') and isinstance(node.annotation, typed_ast.ast3.Str):
            node.annotation = typed_ast.ast3.parse(
                source=node.annotation.s, filename='<annotation>', mode='eval')
            changes += 1
        # parse type comments stored as strings
        if hasattr(node, 'type_comment') and isinstance(node.type_comment, str):
            node.type_comment = typed_ast.ast3.parse(
                source=node.type_comment, filename='<type_comment>', mode='eval')
            changes += 1
    _LOG.info('postprocessed typed Python AST: converted %i attribute(s)', changes)
    #return changes
    return tree


class NativePythonParser(Parser):
    """Python 3 two-in-one lexer and parser based on a built-in Python modules.

    It uses built-in function compile().

    It relies on the following modules:

    - ast  https://docs.python.org/3/library/ast.html

    All of them are described here in detail: https://docs.python.org/3/library/language.html

    Converts code into Python's built-in abstract syntax tree, as defined at
    https://docs.python.org/3/library/ast.html

    Built-in function compile() with flag ast.PyCF_ONLY_AST is used to perform AST creation.
    """

    def __init__(self, default_mode: t.Optional[str] = None, *args, **kwargs):
        super().__init__(Language.find('Python 3'), *args, **kwargs)

        assert default_mode is None or \
            isinstance(default_mode, str) and default_mode in PARSER_MODES_SET

        self.default_mode = default_mode

    def parse(self, code: str, filename: str='<string>', mode: t.Optional[str] = None) -> t.Any:

        if mode is None:
            mode = self.default_mode

        if mode is None:
            return self._parse_with_mode_inference(code, filename)
        else:
            return self._parse(code, filename, mode)

    def _parse_with_mode_inference(self, code: str, filename: str) -> t.Any:
        excluded_modes = set()
        while any((mode not in excluded_modes) for mode in PARSER_MODES_SET):
            inferred_mode = infer_parser_mode(code, excluded_modes)
            try:
                return self._parse(code, filename, inferred_mode)
            except RuntimeError as err:
                excluded_modes.add(inferred_mode)
                _LOG.debug(err, exc_info=1)
        raise RuntimeError('all possible parser modes have been excluded')

    def _parse(self, code, filename, mode) -> ast.AST:
        code = preprocess_python_code(code)
        try:
            # with ast.parse() optimization cannot be set explicitly
            return compile(
                source=code, filename=filename, mode=mode, flags=ast.PyCF_ONLY_AST,
                dont_inherit=True, optimize=0)
        except SyntaxError as err:
            raise RuntimeError('compile() failed in mode="{}"'.format(mode)) from err


class TypedPythonParser(NativePythonParser):

    def _parse(self, code, filename, mode) -> typed_ast.ast3.AST:
        code = preprocess_python_code(code)
        try:
            tree = typed_ast.ast3.parse(source=code, filename=filename, mode=mode)
        except SyntaxError as err:
            raise RuntimeError('typed_ast.ast3.parse() failed in mode="{}"'.format(mode)) from err

        return postprocess_typed_ast(tree)


class TypedPythonParserWithComments(TypedPythonParser):

    def _parse(self, code, filename, mode) -> typed_ast.ast3.AST:
        code = preprocess_python_code(code)
        try:
            tree = horast.parse(code, filename, mode)
        except SyntaxError as err:
            raise RuntimeError('horast.parse() failed in mode="{}"'.format(mode)) from err
        tree = postprocess_typed_ast(tree)
        return tree
