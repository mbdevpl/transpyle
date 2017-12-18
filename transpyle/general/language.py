"""Properties of a programming language."""

import collections.abc
# import logging
import pathlib
import typing as t

from .registry import Registry


# _LOG = logging.getLogger(__name__)
# _TIME = timing.get_timing_group(__name__)

_LANG_NAME_UNRECOGNIZED_MSG = 'language name "{}" is not recognized'


class Language(Registry):

    """Properties of a programming language."""

    def __init__(
            self, names: t.Sequence[str], file_extensions: t.Sequence[str],
            version: t.Optional[tuple] = None):
        """Initialize a Language instance.

        :param names: list of names of the language
        :param file_extensions: file extensions, including the dot
        """
        assert isinstance(names, collections.abc.Sequence), type(names)
        assert names
        assert isinstance(file_extensions, collections.abc.Sequence), type(file_extensions)
        assert file_extensions
        if __debug__:
            for name in names:
                assert isinstance(name, str), type(name)
                assert name
            for file_extension in file_extensions:
                assert isinstance(file_extension, str), type(file_extension)
                assert file_extension
                assert file_extension.startswith('.'), file_extension
        assert isinstance(version, tuple) or version is None

        self.names = [name for name in names]
        self.default_name = self.names[0]
        self.file_extensions = [file_extension.lower() for file_extension in file_extensions]
        self.default_file_extension = self.file_extensions[0]
        self.version = version

    @property
    def lowercase_name(self) -> str:
        return self.default_name.lower()

    def has_name(self, name: str) -> bool:
        assert isinstance(name, str), type(name)
        return name in self.names

    def has_extension(self, file_extension: str) -> bool:
        assert isinstance(file_extension, str), type(file_extension)
        return file_extension.lower() in self.file_extensions

    def has_extension_of(self, path: pathlib.Path) -> bool:
        assert isinstance(path, pathlib.Path), type(path)
        _, file_extension = path.splitext(path)
        return self.has_extension(file_extension)

    def __repr__(self):
        return '<{} language object>'.format(self.default_name)
