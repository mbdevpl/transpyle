"""Binding creator."""

import collections.abc
import importlib
import logging
import pathlib
import sys
import types
import typing as t

from .registry import Registry


_LOG = logging.getLogger(__name__)


class Binder(Registry):

    """Simplify interfacing Python with extension modules."""

    def __init__(self):
        pass

    def bind_module(self, module_name: str) -> types.ModuleType:
        module = importlib.import_module(module_name)
        _LOG.info('successfully imported module "%s"', module.__name__)
        return module

    def bind_object(self, module_name_or_path: t.Union[pathlib.Path, str],
                    object_name: t.Optional[str] = None) -> collections.abc.Callable:
        """Bind a single object (like a class or function) from an extension module."""
        if isinstance(module_name_or_path, pathlib.Path):
            module = self.bind(module_name_or_path)
        elif isinstance(module_name_or_path, str):
            module = self.bind_module(module_name_or_path)
        else:
            raise TypeError('unsupported type {}'.format(type(module_name_or_path)))
        object_names = [var for var in vars(module) if not var.startswith('__')]
        _LOG.debug('interface: %s', ', '.join(object_names))
        if object_name is None:
            assert len(object_names) == 1, object_names
            object_name = object_names[0]

        interface = getattr(module, object_name)
        assert callable(interface)

    def bind(self, path: pathlib.Path) -> types.ModuleType:
        dir_ = str(path.parent)
        while path.suffix:
            path = path.with_suffix('')
        module_name = path.name
        sys.path.insert(0, dir_)
        try:
            _LOG.debug('%s', sys.path)
            module = self.bind_module(module_name)
        except ImportError:
            sys.path.remove(dir_)
            raise
        else:
            sys.path.remove(dir_)
        return module
