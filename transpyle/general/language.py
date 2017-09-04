"""Properties of a programming language."""

import collections.abc
import logging
import os
import typing

from .registry import Registry


_LOG = logging.getLogger(__name__)
    #_TIME = timing.get_timing_group(__name__)

_LANG_NAME_UNRECOGNIZED_MSG = 'language name "{}" is not recognized'

class Language(Registry):
    """Properties of a programming language."""

    def __init__(
            self, names: typing.Sequence[str], file_extensions: typing.Sequence[str],
            version: typing.Optional[tuple]=None):
        """Initialize a Language instance.

        :param names: list of names of the language
        :param file_extensions: file extensions, including the dot
        """

        assert isinstance(names, collections.abc.Sequence)
        assert len(names) >= 1
        assert isinstance(file_extensions, collections.abc.Sequence)
        assert len(file_extensions) >= 1
        if __debug__:
            for name in names:
                assert isinstance(name, str)
                assert len(name) > 0
            for file_extension in file_extensions:
                assert isinstance(file_extension, str)
                assert len(file_extension) > 0
                assert file_extension.startswith('.')
        assert isinstance(version, tuple) or version is None

        self.names = names
        self.default_name = names[0]
        self.file_extensions = file_extensions
        self.default_file_extension = file_extensions[0]
        self.version = version

    @property
    def lowercase_name(self) -> str:

        return self.default_name.lower()

    def has_name(self, name: str) -> bool:

        assert isinstance(name, str)

        return name in self.names

    def has_extension(self, file_extension: str) -> bool:

        assert isinstance(file_extension, str)

        return file_extension in self.file_extensions

    def path_matches_extensions(self, path: str) -> bool:

        assert isinstance(path, str)

        _, file_extension = os.path.splitext(path)

        return self.has_extension(file_extension)
