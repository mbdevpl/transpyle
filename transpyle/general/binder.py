"""Binding creator."""

from .registry import Registry


class Binder(Registry):

    """Interface between compiled binary in different language and Python."""

    def __init__(self, *args, **kwargs):
        raise NotImplementedError()

    def bind(self, compiler_result, *args, **kwargs):
        raise NotImplementedError()
