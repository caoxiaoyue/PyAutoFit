import inspect
import itertools
from collections import Iterable
from hashlib import md5


class Identifier:
    def __init__(self, obj):
        """
        Wraps an object and recursively generates an identifier
        """
        self.hash_list = list()
        self._add_value_to_hash_list(
            obj
        )

    def _add_value_to_hash_list(self, value):
        """
        Add some object and recursively add its children to the hash_list.

        The md5 hash of this object is taken to create an identifier.

        If an object specifies __identifier_fields__ then only attributes
        with a name in this list are included.

        Parameters
        ----------
        value
            An object
        """
        if hasattr(value, "__dict__"):
            d = value.__dict__
            if hasattr(
                    value,
                    "__identifier_fields__"
            ):
                d = {
                    k: v
                    for k, v
                    in d.items()
                    if k in value.__identifier_fields__
                }
            self.add_value_to_hash_list(
                d
            )
        elif isinstance(
                value, dict
        ):
            for key, value in value.items():
                if not (key.startswith("_") or key in ("id", "paths")):
                    self.hash_list.append(key)
                    self.add_value_to_hash_list(
                        value
                    )
        elif isinstance(
                value,
                (str, float, int, bool)
        ):
            self.hash_list.append(
                str(value)
            )
        elif isinstance(value, Iterable):
            for value in value:
                self.add_value_to_hash_list(
                    value
                )

    def add_value_to_hash_list(self, value):
        if isinstance(
                value,
                property
        ):
            return
        if hasattr(
                value,
                "identifier"
        ) and not inspect.isclass(
            value
        ):
            self.hash_list.append(
                value.identifier
            )
        else:
            self._add_value_to_hash_list(
                value
            )

    def __str__(self):
        return md5(".".join(
            self.hash_list
        ).encode("utf-8")).hexdigest()

    def __eq__(self, other):
        return str(self) == str(other)


class ModelObject:
    _ids = itertools.count()

    def __init__(self):
        self.id = next(self._ids)

    @property
    def component_number(self):
        return self.id

    def __hash__(self):
        return self.id

    def __eq__(self, other):
        try:
            return self.id == other.id
        except AttributeError:
            return False

    @property
    def identifier(self):
        return str(Identifier(self))
