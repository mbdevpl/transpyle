"""Source code file reader."""

import collections
import inspect
import os
import pathlib
import typing as t


class CodeReader:

    """Read whole source code files."""

    def __init__(self, extensions: t.Optional[t.Iterable[str]] = None):
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
        self._extensions = extensions

    @property
    def extensions(self) -> t.Sequence[str]:
        return self._extensions

    def read_file(self, path: pathlib.Path) -> str:
        """Read a single file."""
        assert isinstance(path, pathlib.Path), type(path)

        if not path.is_file():
            raise ValueError(f'given path {path} does not lead to a file')
        if self._extensions and path.suffix not in self._extensions:
            raise ValueError(f'incompatible path {path} given to {self}')
        with open(path, 'r') as source_file:
            contents = source_file.read()
        return contents

    def read_folder(
            self, root_path: pathlib.Path, recursive: bool = True) -> t.Dict[pathlib.Path, str]:
        """Read all relevant files in a given directory."""
        assert isinstance(root_path, pathlib.Path), type(root_path)
        assert isinstance(recursive, bool), type(recursive)
        if not root_path.is_dir():
            raise ValueError(f'given path {root_path} does not lead to a folder')
        files = {}
        for folder_path, _, file_names in os.walk(root_path, topdown=True):
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
        return f'{type(self).__qualname__}(extensions={self._extensions})'
