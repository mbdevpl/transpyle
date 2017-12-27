"""Binding compiled Fortran code."""

# import importlib
import logging
# import types

from ..general import Binder


_LOG = logging.getLogger(__name__)


class F2PyBinder(Binder):

    """Bind existing f2py-built extension module."""

    # def bind_module(self, module_name: str) -> types.ModuleType:
    #    module = importlib.import_module(module_name)
    #    _LOG.info('successfully imported f2py module "%s"', module.__name__)
    #    return module

    pass
