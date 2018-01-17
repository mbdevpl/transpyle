"""Non-standard exception types used in transpyle."""


class ContinueIteration(StopIteration):

    """Allows for "continue" keyword within a function called from within a loop."""

    pass
