"""Non-standard exception types used in transpyle."""

class ExternalToolError(Exception):
    """Indicates an issue with an external tool."""


class ExternalToolMissingError(ExternalToolError, FileNotFoundError):
    """Raised when an external tool is not found."""


class ExternalToolVersionError(ExternalToolError, AssertionError):
    """Raised when an external tool doesn't satisfy the version requirements."""


class ContinueIteration(StopIteration):

    """Allows for "continue" keyword within a function called from within a loop."""

    pass


class AstGeneralizationError(RuntimeError):

    pass
