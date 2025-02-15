"""Evaluate external tool and ."""

import pathlib
import shutil

import version_query

from .exc import ExternalToolMissingError, ExternalToolVersionError
from .tools import run_tool


class ExternalTool:
    """Generic tool definition.
    
    When inheriting, the following has to be defined:
    * path: path to the tool
    * _version_arg: argument to get the version of the tool when executing it
    * _version_output_filter: function to filter the output of the version command
    """

    path: pathlib.Path
    _version_arg: str
    _version: version_query.Version | None = None

    @classmethod
    def exists(cls) -> bool:
        path = shutil.which(cls.path.as_posix())
        return path is not None

    @classmethod
    def assert_exists(cls) -> None:
        """Assert that the external tool exists."""
        if not cls.exists():
            raise ExternalToolMissingError(f'{cls.path} not found')

    @classmethod
    def version(cls) -> version_query.Version:
        """Determine the version of the external tool."""
        if cls._version is None:
            result = run_tool(cls.path, [cls._version_arg])
            version_str = cls._version_output_filter(result.stdout)
            cls._version = version_query.Version.from_str(version_str)
        return cls._version

    @classmethod
    def _version_output_filter(cls, output: str) -> str:
        raise NotImplementedError('this method needs to be implemented')

    @classmethod
    def assert_version_at_least(cls, version: version_query.Version) -> None:
        """Assert that the external tool is at least the given version."""
        cls.assert_exists()
        if cls.version() < version:
            raise ExternalToolVersionError(
                f'{cls.path} version {cls.version} does not satisfy the requirement >= {version}')
