from copy import deepcopy
from enum import Enum
from typing import Any, NamedTuple

from attr.validators import deep_mapping


class Action(Enum):
    SET_VALUE = 1
    DELETE = 2


class DictMod(NamedTuple):
    name: str
    action: Action
    value: Any = None


def set_value_mods(*keys: list[str], value: Any) -> list[DictMod]:
    """Return a list of `Action.SET_VALUE` modifications for the given keys,
    using the given value.
    """
    return [DictMod(x, Action.SET_VALUE, value) for x in keys]


def set_none_mods(*keys: list[str]) -> list[DictMod]:
    """Return a list of `Action.SET_VALUE` modifications for the given keys,
    using a value of `None`.
    """
    return set_value_mods(*keys, value=None)


def delete_mods(*keys: list[str]) -> list[DictMod]:
    """Return a list of `Action.DELETE` modification for the given keys.
    """
    return [DictMod(x, Action.DELETE) for x in keys]


def modify_dict(d: dict[str, Any], mods: list[DictMod]) -> None:
    """Apply the modifications to the given dictionary and return it.
    """
    for field, action, value in mods:
        if action == Action.DELETE:
            del d[field]
        elif action == Action.SET_VALUE:
            d[field] = value
        else:
            raise ValueError(f'Invalid action {action} for mod')


def modified_dict(d: dict[str, Any], mods: list[DictMod]) -> dict[str, Any]:
    """Apply the modifications to a copy of the given dictionary and return it.
    """
    d = deepcopy(d)
    modify_dict(d, mods)
    return d


def dict_without(d: dict[str, Any], *keys: list[str]) -> dict[str, Any]:
    """Delete the `id` key from a copy of the given dictionary and return it.
    """
    return modified_dict(d, delete_mods(*keys))
