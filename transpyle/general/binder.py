"""Binding creator."""

import collections.abc
import pathlib
import sys

from .registry import Registry


class Binder(Registry):

    """Interface between compiled binary in different language and Python."""

    def __init__(self):
        pass

    def bind_module(self, module_name: str) -> collections.abc.Callable:
        raise NotImplementedError()

    def bind(self, path: pathlib.Path) -> collections.abc.Callable:
        dir_ = str(path.parent)
        while path.suffix:
            path = path.with_suffix('')
        module_name = path.name
        sys.path.insert(0, dir_)
        try:
            print(sys.path)
            module = self.bind_module(module_name)
        except ModuleNotFoundError:
            sys.path.remove(dir_)
            raise
        else:
            sys.path.remove(dir_)
        return module
