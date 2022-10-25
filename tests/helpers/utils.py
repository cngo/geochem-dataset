from copy import deepcopy
from enum import Enum
from typing import Any, Dict, List, NamedTuple

from attr.validators import deep_mapping


class DeleteField:
    pass


class Action(Enum):
    SET_VALUE = 1
    DELETE = 2


class DictMod(NamedTuple):
    name: str
    action: Action
    value: Any = None


def set_value_mods(*keys: List[str], value: Any) -> List[DictMod]:
    """Return a list of `Action.SET_VALUE` modifications for the given keys,
    using the given value.
    """
    return [DictMod(x, Action.SET_VALUE, value) for x in keys]


def set_none_mods(*keys: List[str]) -> List[DictMod]:
    """Return a list of `Action.SET_VALUE` modifications for the given keys,
    using a value of `None`.
    """
    return set_value_mods(*keys, value=None)


def delete_mods(*keys: List[str]) -> List[DictMod]:
    """Return a list of `Action.DELETE` modification for the given keys.
    """
    return [DictMod(x, Action.DELETE) for x in keys]


def modify_dict(d: Dict[str, Any], mods: List[DictMod]) -> None:
    """Apply the modifications to the given dictionary and return it.
    """
    for field, action, value in mods:
        if action == Action.DELETE:
            del d[field]
        elif action == Action.SET_VALUE:
            d[field] = value
        else:
            raise ValueError(f'Invalid action {action} for mod')


def modified_dict(d: Dict[str, Any], mods: List[DictMod]) -> Dict[str, Any]:
    """Apply the modifications to a copy of the given dictionary and return it.
    """
    d = deepcopy(d)
    modify_dict(d, mods)
    return d


def dict_without(d: Dict[str, Any], *keys: List[str]) -> Dict[str, Any]:
    """Delete the `id` key from a copy of the given dictionary and return it.
    """
    return modified_dict(d, delete_mods(*keys))



def modified_kwargs(kwargs, mods):
    return modified_dict(kwargs, mods)


def kwargs_without_id(kwargs):
    return dict_without(kwargs, 'id')




from openpyxl.utils import get_column_letter


def xlref(row_idx, column_idx, zero_indexed=True):
    return xlcolref(column_idx, zero_indexed) + str(xlrowref(row_idx, zero_indexed))


def xlcolref(column_idx, zero_indexed=True):
    if zero_indexed:
        column_idx += 1
    return get_column_letter(column_idx)


def xlrowref(row_idx, zero_indexed=True):
    if zero_indexed:
        row_idx += 1
    return row_idx
