"""Source code file reader."""

import collections
import os
import typing as t

READ_NOT_FILE_MSG = 'given path "{}" does not lead to a file'
READ_WRONG_EXT_MSG = '"{}" has wrong extension (i.e. not one of: {})'

class CodeReader:

    """Read whole source code files."""

    def __init__(self, extensions: t.Optional[t.Sequence[str]]=None) -> None:
        """Initialize new instance of CodeReader.

        :param extensions: if provided, any files with extensions different than given ones will be
            ignored by the reader when using read_folder() and will cause errors when using
            read_file()
        """

        assert extensions is None or isinstance(extensions, collections.abc.Iterable)
        if __debug__:
            if extensions is not None:
                for extension in extensions:
                    assert isinstance(extension, str), (type(extension), extension, extensions)

        self._extensions = extensions

    @property
    def extensions(self):
        return self._extensions

    def read_file(self, file_path: str) -> str:
        """Read a single file."""

        assert isinstance(file_path, str)

        if not os.path.isfile(file_path):
            raise RuntimeError(READ_NOT_FILE_MSG.format(file_path))
        _, file_extension = os.path.splitext(file_path)
        if self.extensions is not None and file_extension not in self.extensions:
            raise RuntimeError(READ_WRONG_EXT_MSG.format(file_path, self.extensions))
        with open(file_path, 'r') as source_file:
            contents = source_file.read()
            return contents

    def read_folder(self, root_folder_path: str, recursive: bool=True) -> t.Dict[str, str]:
        """Read all relevant files in a given directory."""

        assert isinstance(root_folder_path, str)
        assert isinstance(recursive, bool)

        files = collections.OrderedDict()
        for folder_path, _, file_names in os.walk(root_folder_path, topdown=True):
            for file_name in file_names:
                _, file_extension = os.path.splitext(file_name)
                if self.extensions is not None and file_extension not in self.extensions:
                    continue
                file_path = os.path.join(folder_path, file_name)
                files[file_path] = self.read_file(file_path)
            if not recursive:
                break
        return files

    #def to_default_string(self, indent:int)->str:
    #    return self.to_string(indent, args=[self.extensions], inline=True)

    def __str__(self):
        return f'{type(self).__qualname__}(extensions={self._extensions})'
