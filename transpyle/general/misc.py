"""Various utility functions."""

import collections.abc
import typing as t

import typed_ast.ast3 as typed_ast3


def flatten_sequence(sequence: t.MutableSequence[t.Any]) -> None:
    """Transform a given list of lists of lists (...) of lists into a flat list in-place."""
    assert isinstance(sequence, collections.abc.MutableSequence), type(sequence)
    for i, elem in enumerate(sequence):
        if isinstance(elem, collections.abc.MutableSequence):
            flatten_sequence(elem)
            for value in reversed(elem):
                sequence.insert(i, value)
            del sequence[i + len(elem)]


def flatten_syntax(syntax: t.Union[typed_ast3.AST, t.MutableSequence[t.Any]]) -> None:
    """Flatten all lists of lists within the given syntax in-place."""
    if isinstance(syntax, (typed_ast3.Module, typed_ast3.FunctionDef, typed_ast3.ClassDef,
                           typed_ast3.For, typed_ast3.While, typed_ast3.If, typed_ast3.With,
                           typed_ast3.Try, typed_ast3.ExceptHandler,
                           typed_ast3.AsyncFunctionDef, typed_ast3.AsyncFor, typed_ast3.AsyncWith)):
        for node in syntax.body:
            flatten_syntax(node)
        flatten_sequence(syntax.body)
        return
    if isinstance(syntax, (typed_ast3.For, typed_ast3.While, typed_ast3.If, typed_ast3.Try,
                           typed_ast3.AsyncFor)):
        for node in syntax.orelse:
            flatten_syntax(node)
        flatten_sequence(syntax.orelse)
        return
    if isinstance(syntax, typed_ast3.Try):
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
