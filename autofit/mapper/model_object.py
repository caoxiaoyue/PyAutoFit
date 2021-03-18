import itertools
from collections import Iterable
from hashlib import md5


class Identifier:
    def __init__(self, obj):
        self.hash_list = list()
        self._add_value_to_hash_list(
            obj
        )

    def _add_value_to_hash_list(self, value):
        if hasattr(value, "__dict__"):
            for key, value in value.__dict__.items():
                if not (key.startswith("_") or key == "id"):
                    self.hash_list.append(key)
                    self.add_value_to_hash_list(
                        value
                    )
        elif isinstance(value, Iterable):
            for value in value:
                self.add_value_to_hash_list(
                    value
                )
        elif isinstance(
                value,
                (str, float, int)
        ):
            self.hash_list.append(
                str(value)
            )

    def add_value_to_hash_list(self, value):
        if hasattr(value, "identifier"):
            self.hash_list.append(
                value.identifier
            )
        else:
            self._add_value_to_hash_list(
                value
            )
        self._add_value_to_hash_list(value)
        return md5(".".join(
            self.hash_list
        ).encode("utf-8")).hexdigest()

    def __str__(self):
        return md5(".".join(
            self.hash_list
        ).encode("utf-8")).hexdigest()


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
