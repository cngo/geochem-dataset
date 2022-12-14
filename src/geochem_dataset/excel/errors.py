from __future__ import annotations
from typing import TYPE_CHECKING

from geochem_dataset.excel.utils import xlcolref

if TYPE_CHECKING:
    from geochem_dataset.excel.dataset import Dataset
    from geochem_dataset.excel.utils import Workbook, Worksheet


class WorksheetError(Exception):
    def __init__(self, message, *, ds: "Dataset", wb: Workbook, ws: Worksheet):
        self.dataset = ds
        self.workbook = wb
        self.worksheet = ws
        super().__init__(self, message)

    @property
    def message(self):
        return self.args[0]

    def __str__(self):
        return f"[ds:{self.dataset.name}][wb:{self.workbook.name}][ws:{self.worksheet.name}]: {self.message}"


class MissingHeadingsError(WorksheetError):
    MESSAGE_TEMPLATE = "Missing heading for column(s) indexes: {column_xl_indexes}"

    def __init__(self, *, ds: Dataset, wb: Workbook, ws: Worksheet, column_indexes: list[int] = None, column_xl_indexes: list[str] = None):
        assert column_indexes ^ column_xl_indexes

        if column_indexes:
            column_xl_indexes = list(map(xlcolref, column_xl_indexes))

        message = self.MESSAGE_TEMPLATE.format(column_xl_indexes=column_xl_indexes)
        super().__init__(message, ds=ds, wb=wb, ws=ws)


class MissingColumnsError(WorksheetError):
    MESSAGE_TEMPLATE = "Missing columns: {columns}"

    def __init__(self, *, ds: Dataset, wb: Workbook, ws: Worksheet, columns: list[str]):
        message = self.MESSAGE_TEMPLATE.format(columns=columns)
        super().__init__(message, ds=ds, wb=wb, ws=ws)


class ExtraColumnsError(WorksheetError):
    MESSAGE_TEMPLATE = "Extra columns: {columns}"

    def __init__(self, *, ds: Dataset, wb: Workbook, ws: Worksheet, columns: list[str]):
        message = self.MESSAGE_TEMPLATE.format(columns=columns)
        super().__init__(message, ds=ds, wb=wb, ws=ws)






class InvalidDatasetNameError(Exception):
    pass


class ExtraColumnsError(Exception):
    pass


class MissingColumnsError(Exception):
    pass


class IncorrectNumberOfRowsError(Exception):
    def __init__(self, *args, min_rows=None, max_rows=None):
        self.min_rows = min_rows
        self.max_rows = max_rows












class IntegrityError(Exception):
    def __init__(self, message, **kwargs):
        self.__dict__.update(kwargs)
        Exception.__init__(self, message)

    @property
    def message(self):
        return self.args[0]

    def __str__(self):
        return f"{self.dataset}[{self.workbook}][{self.worksheet}]: {self.message}"







class DuplicateAnalysisResultParametersError(IntegrityError):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __str__(self):
        cells = ', '.join(self.cells)
        other_cells = ', '.join(self.other_cells)

        if len(cells) > 20:
            cells = cells[:17] + "..."

        if len(other_cells) > 20:
            other_cells = other_cells[:17] + "..."

        return f"{self.dataset}[{self.workbook}][{self.worksheet}][{cells}]: Parameters for results violate unique constraint (duplicate of parameters for result in cells {other_cells} of worksheet \"{self.other_worksheet}\""
