"""Binding compiled Fortran code."""

import collections.abc
import importlib
import logging

from ..general import Binder


_LOG = logging.getLogger(__name__)


class F2PyBinder(Binder):

    """Bind existing f2py-built extension module."""

    def bind_module(self, module_name: str) -> collections.abc.Callable:
        module = importlib.import_module(module_name)
        function_names = [var for var in vars(module) if not var.startswith('__')]
        if __debug__:
            _LOG.info('successfully imported f2py module "%s"', module.__name__)
            _LOG.debug('interface: %s', ', '.join(function_names))

        assert len(function_names) == 1, function_names
        function_name = function_names[0]
        interface = getattr(module, function_name)

        assert callable(interface)
        return interface
