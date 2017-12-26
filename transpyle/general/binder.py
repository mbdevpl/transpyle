"""Binding creator."""

import collections.abc
import pathlib

from .registry import Registry


class Binder(Registry):

    """Interface between compiled binary in different language and Python."""

    def __init__(self):
        pass

    def bind_module(self, module_name: str) -> collections.abc.Callable:
        raise NotImplementedError()

    def bind(self, path: pathlib.Path) -> collections.abc.Callable:
        module_name = path.name
        return self.bind_module(module_name)
