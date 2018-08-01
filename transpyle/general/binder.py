"""Binding creator."""

# import collections.abc
import contextlib
import importlib
import logging
import pathlib
import sys
import types
import typing as t

from .registry import Registry

_LOG = logging.getLogger(__name__)


@contextlib.contextmanager
def insert_to_sys_path(path: t.Union[pathlib.Path, str]):
    """Context manager for temporarily inserting an entry at the beginning of sys.path."""
    path_str = str(path)
    sys.path.insert(0, path_str)
    _LOG.warning('modified sys.path: inserted "%s"', path)
    _LOG.debug('current sys.path: %s', sys.path)
    try:
        yield
    finally:
        assert sys.path[0] == path_str
        del sys.path[0]
        _LOG.warning('modified sys.path: removed "%s"', path)


class Binder(Registry):

    """Simplify interfacing Python with extension modules."""

    def __init__(self):
        pass

    def bind_module(self, module_name: str) -> types.ModuleType:
        """Bind a module by name."""
        assert isinstance(module_name, str), type(module_name)
        module = importlib.import_module(module_name)
        _LOG.info('successfully imported module "%s"', module.__name__)
        return module

    def _unbind_module(self, module: types.ModuleType) -> None:
        assert sys.modules[module.__name__] is module
        del sys.modules[module.__name__]

    def bind_path(self, path: pathlib.Path) -> types.ModuleType:
        """Bind a module by path."""
        assert isinstance(path, pathlib.Path), type(path)
        while path.suffix:
            path = path.with_suffix('')
        with insert_to_sys_path(path.parent):
            module = self.bind_module(path.name)
        return module

    def bind(self, module_name_or_path: t.Union[pathlib.Path, str]) -> types.ModuleType:
        """Bind a module by name or path."""
        if isinstance(module_name_or_path, pathlib.Path):
            module = self.bind_path(module_name_or_path)
        elif isinstance(module_name_or_path, str):
            module = self.bind_module(module_name_or_path)
        else:
            raise TypeError('unsupported type {}'.format(type(module_name_or_path)))
        return module

    @contextlib.contextmanager
    def temporarily_bind(self, module_name_or_path):
        """Bind a module and then automatically unbind it when the context ends."""
        module = self.bind(module_name_or_path)
        yield module
        self._unbind_module(module)

    def _bind_object(self, module: types.ModuleType, object_name: t.Optional[str]) -> object:
        object_names = [var for var in vars(module) if not var.startswith('__')]
        _LOG.debug('interface: %s', ', '.join(object_names))
        if object_name is None:
            if len(object_names) != 1:
                raise ValueError('module has to contain exactly one object for it to be default,'
                                 ' but module {} contains {}: {}'.format(module, len(object_names),
                                                                         object_names))
            object_name = object_names[0]

        interface = getattr(module, object_name)
        # assert callable(interface), interface
        return interface

    def bind_object(self, module_name_or_path: t.Union[pathlib.Path, str],
                    object_name: t.Optional[str] = None) -> object:
        """Bind a single object (like a class or function) from a module."""
        module = self.bind(module_name_or_path)
        return self._bind_object(module, object_name)

    @contextlib.contextmanager
    def temporarily_bind_object(self, module_name_or_path, object_name=None):
        """Bind a module to get an object from it and then unbind it when the context ends."""
        module = self.bind(module_name_or_path)
        obj = self.bind_object(module_name_or_path, object_name)
        yield obj
        self._unbind_module(module)
