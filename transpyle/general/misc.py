"""Various utility functions."""

import ast
import collections.abc
import typing as t

import typed_ast.ast3 as typed_ast3


def dict_mirror(dict_: dict):
    return {value: key for key, value in dict_.items() if value is not None}


def flatten_sequence(sequence: t.MutableSequence[t.Any]) -> None:
    """Transform a given list of lists of lists (...) of lists into a flat list in-place."""
    assert isinstance(sequence, collections.abc.MutableSequence), type(sequence)
    for i, elem in enumerate(sequence):
        if isinstance(elem, collections.abc.MutableSequence):
            flatten_sequence(elem)
            for value in reversed(elem):
                sequence.insert(i, value)
            del sequence[i + len(elem)]


def make_flatten_syntax(ast_module):

    def flatten_syntax(syntax: t.Union[ast_module.AST, t.MutableSequence[t.Any]]) -> None:
        """Flatten all lists of lists within the given syntax in-place."""
        if isinstance(syntax, (ast_module.Module, ast_module.FunctionDef, ast_module.ClassDef,
                               ast_module.For, ast_module.While, ast_module.If, ast_module.With,
                               ast_module.Try, ast_module.ExceptHandler,
                               ast_module.AsyncFunctionDef, ast_module.AsyncFor,
                               ast_module.AsyncWith)):
            for node in syntax.body:
                flatten_syntax(node)
            flatten_sequence(syntax.body)
            return
        if isinstance(syntax, (ast_module.For, ast_module.While, ast_module.If, ast_module.Try,
                               ast_module.AsyncFor)):
            for node in syntax.orelse:
                flatten_syntax(node)
            flatten_sequence(syntax.orelse)
            return
        if isinstance(syntax, ast_module.Try):
            for node in syntax.handlers:
                flatten_syntax(node)
            # flatten_sequence(syntax.handlers)  # unnecessary
            for node in syntax.finalbody:
                flatten_syntax(node)
            flatten_sequence(syntax.finalbody)
            return
        if not isinstance(syntax, collections.abc.MutableSequence):
            return
        for node in syntax:
            flatten_syntax(node)
        flatten_sequence(syntax)

    return flatten_syntax


flatten_syntax = {ast_module: make_flatten_syntax(ast_module) for ast_module in (ast, typed_ast3)}
