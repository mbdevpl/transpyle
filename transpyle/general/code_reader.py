"""Source code file reader."""

import collections
import inspect
import os
import pathlib
import typing as t


class CodeReader:

    """Read whole source code files."""

    def __init__(self, extensions: t.Iterable[str] = None):
        """Initialize new instance of CodeReader.

        :param extensions: if provided, any files with extensions different than given ones will be
            ignored by the reader when using read_folder() and will cause errors when using
            read_file()
        """
        if extensions is None:
            extensions = []
        assert isinstance(extensions, collections.abc.Iterable), type(extensions)
        if __debug__:
            for extension in extensions:
                assert isinstance(extension, str), (type(extension), extension, extensions)
                assert len(extension) > 1 and extension[0] == '.', extension
        self._extensions = {extension for extension in extensions}

    @property
    def extensions(self) -> t.Sequence[str]:
        return self._extensions

    def read_file(self, path: pathlib.Path) -> str:
        """Read a single file."""
        assert isinstance(path, pathlib.Path), type(path)

        if self._extensions and path.suffix not in self._extensions:
            raise ValueError('incompatible path {} given to {}'.format(path, self))
        with path.open() as source_file:
            contents = source_file.read()
        return contents

    def read_folder(
            self, root_path: pathlib.Path, recursive: bool = True) -> t.Dict[pathlib.Path, str]:
        """Read all relevant files in a given directory."""
        assert isinstance(root_path, pathlib.Path), type(root_path)
        assert isinstance(recursive, bool), type(recursive)

        def raise_err(err):
            raise err

        files = {}
        for folder_path, _, file_names in os.walk(str(root_path), topdown=True, onerror=raise_err):
            for file_name in file_names:
                file_path = pathlib.Path(folder_path, file_name)
                if not self._extensions or file_path.suffix in self._extensions:
                    files[file_path] = self.read_file(file_path)
            if not recursive:
                break
        return files

    @staticmethod
    def read_function(function: collections.abc.Callable) -> str:
        assert isinstance(function, collections.abc.Callable), type(function)
        return inspect.getsource(function)

    def __str__(self):
        return '{}(extensions={})'.format(type(self).__qualname__, self._extensions)
