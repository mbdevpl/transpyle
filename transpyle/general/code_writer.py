"""Source code file writers."""

import pathlib
import typing as t


class CodeWriter:

    """Output source code to files."""

    def __init__(self, extension: t.Optional[str] = None):
        assert extension is None or isinstance(extension, str), type(extension)
        assert extension is None or len(extension) > 1 and extension[0] == '.', extension
        self._extension = extension

    @property
    def extension(self) -> t.Optional[str]:
        return self._extension

    def write_file(self, code: str, path: pathlib.Path) -> None:
        """Write a single file."""
        assert isinstance(code, str), type(code)
        assert isinstance(path, pathlib.Path), type(path)
        if self._extension is not None and path.suffix != self._extension:
            raise ValueError('incompatible path {} given to {}'.format(path, self))
        with open(str(path), 'w') as target_file:
            target_file.write(code)

    def write_module(self, code: str, module_name: str) -> pathlib.Path:
        """Write the code to a single file."""
        assert isinstance(code, str), type(code)
        assert isinstance(module_name, str), type(module_name)
        assert self._extension is not None, 'this writer has no defined file extension'
        path = pathlib.Path(module_name + self._extension)
        self.write_file(code, path)
        return path

    def __str__(self):
        return '{}(extension={})'.format(type(self).__qualname__, self._extension)
