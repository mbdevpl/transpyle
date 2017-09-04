"""Source code file writers."""

import logging
import typing as t

if __debug__:
    _LOG = logging.getLogger(__name__)

class CodeWriter:

    def __init__(self, extension: str):

        assert isinstance(extension, str)

        self._extension = extension

    def write(
            self, code: str, module_name: t.Optional[str]=None,
            path: t.Optional[str]=None) -> str:

        assert isinstance(code, str)
        assert isinstance(module_name, str) or module_name is None
        assert isinstance(path, str) or path is None
        assert (module_name is not None) ^ (path is not None), (module_name, path)

        if path is None:
            path = module_name + self._extension
        else:
            if not path.endswith(self._extension):
                raise RuntimeError(
                    'the path "{}" given to this CodeWriter does not end with "{}"'
                    .format(path, self._extension))
        with open(path, 'w') as f:
            f.write(code)
        return path

    def __str__(self):
        return f'{type(self).__qualname__}(extension={self._extension})'
