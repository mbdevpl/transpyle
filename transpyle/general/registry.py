"""Registry of objects which can be queried."""

import typing as t


class Registry:

    """General-purpose registry of objects."""

    registered = None

    @classmethod
    def register(cls, member, keys) -> None:
        if cls.registered is None:
            cls.registered = {}
        for key in keys:
            cls.registered[key] = member

    @classmethod
    def find(cls, key) -> t.Any:
        if cls.registered is None:
            return None
        return cls.registered.get(key, None)
