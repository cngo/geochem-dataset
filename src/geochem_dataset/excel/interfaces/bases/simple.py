from __future__ import annotations
from abc import ABC
import dataclasses
from decimal import Decimal
import re

import numpy as np
import pandas as pd

from geochem_dataset.excel.exceptions import IntegrityError
from geochem_dataset.excel.interfaces import xlref, xlrowref, xlcolref


class SimpleExcelWorkbookInterface(ABC):
    """An abstract interface for reading an Excel file with one worksheet
    and a simple table structure: first row are headings and subsequent rows
    are data.

    The interface provides simple validation: expected sheet name, expected
    column names, unique constraints, foreign key constraints, min/max data
    rows.

    """

    def __init__(self, dataset):
        self._dataset = dataset

        self._load_dataframe()
        self._validate()
        self._build_items()

    @property
    def path(self):
        return self._dataset.path / self._name

    def get_by(self, **kwargs):
        fields = tuple(sorted(kwargs.keys()))

        index_ = self._items_indexes[fields]
        values = tuple(kwargs[field] for field in fields)

        item_idx = index_[values]
        return self._items[item_idx]

    def __iter__(self):
        for item in self._items:
            yield item

    def _load_dataframe(self):
        try:
            self._df = pd.read_excel(self.path, sheet_name=self._sheet_name)
        except ValueError as e:
            if e.args[0] == f"Worksheet named '{self._sheet_name}' not found":
                workbook = self._name
                worksheet = self._sheet_name
                raise IntegrityError(f'Worksheet {worksheet} is missing from workbook {workbook}')
            else:
                raise e

        self._df = self._df.replace({np.nan: None})

    def _validate(self):
        self._validate_columns()
        self._validate_row_count()
        self._validate_data()

    def _validate_columns(self):
        given_columns = list(self._df.columns)
        expected_columns = list(self._columns)

        missing_columns = set(expected_columns) - set(given_columns)

        if missing_columns:
            worksheet = f'{self._name}::{self._sheet_name}'
            column_names = ', '.join(sorted(missing_columns))
            raise IntegrityError(f'Worksheet {worksheet} is missing columns: {column_names}')

        if not self._dataset.extra_columns_ok:
            unexpected_columns = set(given_columns) - set(expected_columns)

            if unexpected_columns:
                worksheet = f'{self._name}::{self._sheet_name}'
                column_names = ', '.join(sorted(unexpected_columns))
                raise IntegrityError(f'Worksheet {worksheet} has extra columns: {column_names}')

    def _validate_row_count(self):
        min_rows = self._min_count
        max_rows = self._max_count

        row_count = len(self._df.index)

        if min_rows and row_count < min_rows:
            worksheet = f'{self._name}::{self._sheet_name}'
            raise IntegrityError(f'Worksheet {worksheet} has too few rows (min is {min_rows} and max is {"unlimited" if max_rows is None else max_rows})')

        if max_rows and row_count > max_rows:
            worksheet = f'{self._name}::{self._sheet_name}'
            raise IntegrityError(f'Worksheet {worksheet} has too many rows (min is {min_rows} and max is {"unlimited" if max_rows is None else max_rows})')

    def _validate_data(self):
        for idx, row in self._df.iterrows():
            self._validate_row_foreign_key_constraints(idx, row)
            self._validate_row_unique_constraints(idx)

    def _validate_row_foreign_key_constraints(self, row_idx, row):
        for column, foreign_key in self._foreign_key_constraints:
            fk_interface_attr_name, fk_column = foreign_key.split('.')
            fk_interface = getattr(self._dataset, fk_interface_attr_name)

            for fk_row in iter(fk_interface):
                if row[column] == getattr(fk_row, fk_column):
                    break
            else:
                worksheet = f'{self._name}::{self._sheet_name}'
                fk_worksheet = f'{fk_interface._name}::{fk_interface._sheet_name}'
                row = xlrowref(row_idx)
                raise IntegrityError(f'Row 2 of worksheet {worksheet} violated a foreign constraint on column {column} (references column {fk_column.upper()} in worksheet {fk_worksheet})')

    def _validate_row_unique_constraints(self, row_idx):
        for unique_columns in self._unique_constraints:
            df = self._df.loc[:, unique_columns]

            row = df.loc[row_idx]
            row_values = row.values.tolist()

            previous_rows = df.loc[:row_idx-1]
            previous_row_values = previous_rows.values.tolist()

            if row_values in previous_row_values:
                other_row_idx = previous_row_values.index(row_values)

                worksheet = f'{self._name}::{self._sheet_name}'
                row_idx_xl = xlrowref(row_idx + 1)
                columns = ', '.join(unique_columns)
                other_row_idx_xl = xlrowref(other_row_idx + 1)

                raise IntegrityError(f'Row {row_idx_xl} of worksheet {worksheet} violated a unique constraint on columns: {columns} (duplicate of row {other_row_idx_xl})')

    def _build_items(self):
        self._items = []
        self._items_indexes = {
            tuple(sorted(fields)): {}
            for fields in self._dataclass_indexes
        }

        for row_idx, row in self._df.iterrows():
            # Init kwargs with expected columns

            kwargs = {k.lower(): v for k, v in row.to_dict().items() if k in self._columns}

            # Rename kwargs if necessary

            if hasattr(self, '_column_dataclass_field_map'):
                for column, field in self._column_dataclass_field_map:
                    kwargs[field] = kwargs[column.lower()]
                    del kwargs[column.lower()]

            # Cast kwargs if necessary

            for column_idx, field in enumerate(dataclasses.fields(self._dataclass)):
                if field.name in kwargs and kwargs[field.name] is not None and \
                        not isinstance(kwargs[field.name], field.type):
                    try:
                        kwargs[field.name] = field.type(kwargs[field.name])
                    except ValueError as e:
                        worksheet = f'{self._name}::{self._sheet_name}'
                        row = xlrowref(row_idx + 1)
                        column = field.name.upper() if field.name.upper() in self._columns else None
                        raise IntegrityError(f'Row {row} in worksheet {worksheet} has an invalid value for column {column}')

            # Set foreign key kwargs

            for column, fk in self._foreign_key_constraints:
                fk_interface_attr_name, fk_field = fk.split('.')
                fk_interface = getattr(self._dataset, fk_interface_attr_name)
                fk_get_by_fn = getattr(fk_interface, f'get_by_{fk_field}')
                fk_item = fk_get_by_fn(kwargs[column.lower()])

                field = re.sub(r'(?<!^)(?=[A-Z])', '_', type(fk_item).__name__).lower()
                kwargs[field] = fk_item

                del kwargs[column.lower()]

            # Add extra columns to extra field

            extra_columns = set(self._df.columns) - set(self._columns)
            kwargs['extra'] = dict((str(x).lower(), str(row[x])) for x in extra_columns)

            # Create the item

            item = self._dataclass(**kwargs)
            self._items.append(item)

            # Update indexes

            item_idx = len(self._items) - 1

            for fields, index_ in self._items_indexes.items():
                values = tuple(getattr(item, x) for x in fields)
                index_[values] = item_idx
