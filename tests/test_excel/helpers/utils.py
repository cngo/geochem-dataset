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
