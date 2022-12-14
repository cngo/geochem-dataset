from copy import deepcopy
from enum import Enum
import re
from typing import Any, Dict, List, Literal, NamedTuple

from openpyxl.utils import get_column_letter


###############################################################################
# Utilities for modifying dictionaries
###############################################################################


DICT_MOD_SET = "set"
DICT_MOD_DELETE = "delete"

DictModActionValue = Literal[DICT_MOD_SET, DICT_MOD_DELETE]


class DictMod(NamedTuple):
    name: str
    action: DictModActionValue
    value: Any = None


# Functions for creating mods


def set_mod(key: str, value: Any) -> DictMod:
    """Return a `DictMod` that sets a key to a value.
    """
    return DictMod(key, DICT_MOD_SET, value)


def set_mods(*keys: str, value: Any) -> List[DictMod]:
    """Return a list of `DictMod`s setting all keys to the given value.
    """
    return [set_mod(x, value) for x in keys]


def set_none_mods(*keys: str) -> List[DictMod]:
    """Return a list of `DictMod`s setting all keys to `None`.
    """
    return set_mods(*keys, value=None)


def delete_mod(key: str) -> DictMod:
    """Return a `DictMod` that deletes a key.
    """
    return DictMod(key, DICT_MOD_DELETE)


def delete_mods(*keys: str) -> List[DictMod]:
    """Return a list of `DictMod`s deleting all keys.
    """
    return [delete_mod(x) for x in keys]


# Functions for applying mods


def modify_dict(d: Dict[str, Any], mods: List[DictMod]) -> None:
    """Apply mods to a dictionary.
    """
    for key, action, value in mods:
        if action == DICT_MOD_DELETE:
            del d[key]
        elif action == DICT_MOD_SET:
            d[key] = value
        else:
            raise ValueError(f'Invalid action {action} for mod')


def modified_dict(d: Dict[str, Any], mods: List[DictMod]) -> Dict[str, Any]:
    """Copy a dictionary, apply mods to and return it.
    """
    d = deepcopy(d)
    modify_dict(d, mods)
    return d


def dict_without(d: Dict[str, Any], *keys: str) -> Dict[str, Any]:
    """Delete keys from a copy of the given dictionary and return it.
    """
    return modified_dict(d, delete_mods(*keys))


###############################################################################
# Utilities for Excel files
###############################################################################


def xlref(row_idx, column_idx, zero_indexed=True) -> str:
    return xlcolref(column_idx, zero_indexed) + str(xlrowref(row_idx, zero_indexed))


def xlcolref(column_idx, zero_indexed=True) -> str:
    if zero_indexed:
        column_idx += 1
    return get_column_letter(column_idx)


def xlrowref(row_idx, zero_indexed=True) -> int:
    if zero_indexed:
        row_idx += 1
    return row_idx


def parse_cell(cell: str) -> tuple[str]:
    m = re.match('^([A-Z]+)([0-9]+)$', cell)
    return m.groups()
