from abc import ABC
import dataclasses
import re

import numpy as np
from openpyxl.utils import get_column_letter
import pandas as pd

from ..dataclasses import Result
from ..exceptions import IntegrityError

NA_VALUES = ['-1.#IND', '1.#QNAN', '1.#IND', '-1.#QNAN', '#N/A N/A', '#N/A', 'N/A', 'n/a', '<NA>', '#NA', 'NULL', 'null', 'NaN', '-NaN', 'nan', '-nan', '']


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
            kwargs['extra'] = frozenset((str(x).lower(), str(row[x])) for x in extra_columns)

            # Create the item

            item = self._dataclass(**kwargs)
            self._items.append(item)

            # Update indexes

            item_idx = len(self._items) - 1

            for fields, index_ in self._items_indexes.items():
                values = tuple(getattr(item, x) for x in fields)
                index_[values] = item_idx


class AnalysisExcelWorkbookInterface(ABC):
    def __init__(self, dataset):
        self._dataset = dataset

        self._worksheet_names = pd.ExcelFile(self.path).sheet_names

        self._load_worksheets()
        self._validate_worksheets()

    def _load_worksheets(self):
        self._worksheets = [
            AnalysisExcelWorksheetInterface(self, name)
            for name in self._worksheet_names
        ]

    def _validate_worksheets(self):
        pass # TODO

    @property
    def dataset(self):
        return self._dataset

    @property
    def path(self):
        return self._dataset.path / self._name

    def __iter__(self):
        for ws in self._worksheets:
            for result in ws:
                yield result


class AnalysisExcelWorksheetInterface:
    """
    |----------|-------------|-----|-------------------|-----------------|---------------|-----|---------------|
    | SAMPLE   | SUBSAMPLE   | ... | SUB...SUBSAMPLE   | METADATA_TYPE   | result_type_1 | ... | result_type_y |
    |----------|-------------|-----|-------------------|-----------------|---------------|-----|---------------|
    |          |             |     |                   | metadata_type_1 | metadata_1_1  | ... | metadata_1_y  |
    |          |             |     |                   | ...             | ...           | ... | ...           |
    |          |             |     |                   | metadata_type_z | metadata_z_1  | ... | metadata_z_y  |
    |----------|-------------|-----|-------------------|-----------------|---------------|-----|---------------|
    | sample_1 | subsample_1 | ... | sub...subsample_1 |                 | result_1_1    | ... | result_1_y    |
    | ...      | ...         | ... | ...               |                 | ...           | ... | ...           |
    | sample_x | subsample_x | ... | sub...subsample_x |                 | result_x_1    | ... | result_x_y    |
    |----------|-------------|-----|-------------------|-----------------|---------------|-----|---------------|

    The following outlines the steps involved in parsing the file:

    1. The first row must meet the following requirements:

        - The first two columns must be "SAMPLE" and "SUBSAMPLE" and then followed by zero or more deeper subsample
          columns.
        - The next column must be "METADATA_TYPE".
        - The next zero or more columns are result types.

    2. The metadata type column must meet the following requirements:

        - Zero or more metadata types must be given in the rows immediately following the "METADATA_TYPE" heading.
        - The remaining rows must be empty.

    3. The subsample columns must meet the following requirements:

        - Zero or more subsamples must be given in the rows immediately following the last metadata type.
        - The remaining rows must be empty.

    4. Each result type column must meet the following requirements:

        - Metadata values corresponding to the metadata types of their respective rows must be given. Values can empty.
        - Results corresponding to the subsamples of their respective rows must be given. Values can be empty.
        - The remaining rows must be empty.

    """

    def __init__(self, wb, name):
        self._wb = wb
        self._name = name

        self._load_dataframe()
        self._compute_geometry()
        self._validate_dataframe()

    def _load_dataframe(self):
        self._df = pd.read_excel(self._wb.path, header=None, keep_default_na=False, na_values=NA_VALUES, sheet_name=self._name)
        self._df = self._df.replace({np.nan: None})

    def _compute_geometry(self):
        self._geometry = {
            'subsamples': {},
            'metadata_types': {},
            'result_types': {},
        }

        self._compute_subsamples_column_idx_slice()
        self._compute_metadata_types_column_idx()
        self._compute_result_types_column_idx_slice()
        self._compute_metadata_types_row_idx_slice()
        self._compute_subsamples_row_idx_slice()

    def _compute_subsamples_column_idx_slice(self):
        # The subsample columns are minimally the first two columns with
        # specific headings. Additional columns have headings prepended with
        # "SUB" again and again.

        first_row = self._df.iloc[0]

        if first_row[0] != 'SAMPLE':
            raise IntegrityError(f'Cell A1 of worksheet {self._wb.path.name}::{self._name} must be SAMPLE')

        if first_row[1] != 'SUBSAMPLE':
            raise IntegrityError(f'Cell B1 of worksheet {self._wb.path.name}::{self._name} must be SUBSAMPLE')

        column_idx_stop = 2

        for column_idx, heading in first_row.iloc[2:].items():
            expected_heading = 'SUB' + first_row[column_idx - 1]

            if heading != expected_heading:
                break

            column_idx_stop = column_idx_stop + 1

        self._geometry['subsamples']['column_idx_slice'] = slice(0, column_idx_stop)

    def _compute_metadata_types_column_idx(self):
        # The metadata types column is expected to be the column following the
        # last subsample column.

        metadata_type_column_idx = self._geometry['subsamples']['column_idx_slice'].stop

        if metadata_type_column_idx not in self._df.columns or self._df.iloc[0, metadata_type_column_idx] != 'METADATA_TYPE':
            raise IntegrityError(f'Cell C1 of worksheet {self._wb.path.name}::{self._name} must be METADATA_TYPE')

        self._geometry['metadata_types']['column_idx'] = metadata_type_column_idx

    def _compute_result_types_column_idx_slice(self):
        # The result type columns are all columns following the metdata types
        # column.

        column_idx_start = self._geometry['metadata_types']['column_idx'] + 1
        column_idx_stop = len(self._df.iloc[0])

        self._geometry['result_types']['column_idx_slice'] = slice(column_idx_start, column_idx_stop)

    def _compute_metadata_types_row_idx_slice(self):
        # The metadata type rows fall between the heading row and the first
        # subsample row.

        s = self._df.iloc[1:, self._geometry['metadata_types']['column_idx']]
        key = s.notnull()
        row_idx_stop = 1 if s[key].empty else (s[key].index[-1] + 1)

        self._geometry['metadata_types']['row_idx_slice'] = slice(1, row_idx_stop)

    def _compute_subsamples_row_idx_slice(self):
        # The subsample rows begin with the row following the last metadata type
        # and end with the last row of the table.

        row_idx_start = self._geometry['metadata_types']['row_idx_slice'].stop

        self._geometry['subsamples']['row_idx_slice'] = slice(row_idx_start, len(self._df))

    def _validate_dataframe(self):
        self._validate_subsamples()
        self._validate_metadata_types()
        self._validate_result_types()
        self._validate_empty_regions()

    def _validate_subsamples(self):
        subsamples_df = self._df.iloc[self._geometry['subsamples']['row_idx_slice'], self._geometry['subsamples']['column_idx_slice']]
        samples = [str(x.name).strip() for x in iter(self._wb.dataset.samples)]

        for row_idx, subsample_s in subsamples_df.iterrows():
            # Check if any subsample fields are not given

            if subsample_s.isna().any():
                worksheet = f'{self._wb.path.name}::{self._name}'
                row = xlrowref(row_idx)
                raise IntegrityError(f'Missing value(s) for subsample in row {row} of worksheet {self._wb.path.name}::{self._name}')

            # Check if SAMPLE field does not exist in samples file

            sample = str(subsample_s[0]).strip()

            if sample not in samples:
                worksheet = f'{self._wb.path.name}::{self._name}'
                cell = xlref(row_idx, 0)
                raise IntegrityError(f'Sample in cell {cell} of worksheet {worksheet} does not exist')

            # Check if subsample is a duplicate

            previous_subsamples_df = self._df.iloc[self._geometry['subsamples']['row_idx_slice'].start:row_idx, self._geometry['subsamples']['column_idx_slice']]
            previous_subsamples = [tuple(x) for x in previous_subsamples_df.to_numpy()]

            if tuple(subsample_s) in previous_subsamples:
                worksheet = f'{self._wb.path.name}::{self._name}'
                row = xlrowref(row_idx)
                raise IntegrityError(f'Subsample in row {row} of worksheet {worksheet} is a duplicate')

    def _validate_metadata_types(self):
        metadata_types = self._df.iloc[self._geometry['metadata_types']['row_idx_slice'], self._geometry['metadata_types']['column_idx']]

        for row_idx, metadata_type in metadata_types.items():
            # Check if metadata type is not given

            if metadata_type is None:
                worksheet = f'{self._wb.path.name}::{self._name}'
                cell = xlref(row_idx, self._geometry['metadata_types']['column_idx'])
                raise IntegrityError(f'Metadata type is missing in cell {cell} of worksheet {worksheet}')

            # Check if metadata type is a duplicate

            previous_metadata_types = self._df.iloc[self._geometry['metadata_types']['row_idx_slice'].start:row_idx, self._geometry['metadata_types']['column_idx']]

            if metadata_type in tuple(previous_metadata_types):
                worksheet = f'{self._wb.path.name}::{self._name}'
                cell = xlref(row_idx, self._geometry['metadata_types']['column_idx'])
                raise IntegrityError(f'Metadata type in cell {cell} of worksheet {worksheet} is a duplicate')

    def _validate_result_types(self):
        result_types_column_idx_slice = self._geometry['result_types']['column_idx_slice']
        metadata_types_row_idx_slice = self._geometry['metadata_types']['row_idx_slice']

        result_type_metadata_df = self._df.iloc[:metadata_types_row_idx_slice.stop, result_types_column_idx_slice]

        for col_idx, result_type_metadata_s in result_type_metadata_df.items():
            # Check if result type is not given

            if result_type_metadata_s[0] is None:
                worksheet = f'{self._wb.path.name}::{self._name}'
                cell = xlref(0, col_idx)
                raise IntegrityError(f'Result type in cell {cell} of worksheet {worksheet} is missing')

            # Check if result type / metadata pair is a duplicate

            if result_type_metadata_s.values.tolist() in result_type_metadata_df.loc[:, :col_idx-1].transpose().values.tolist():
                worksheet = f'{self._wb.path.name}::{self._name}'
                column = xlcolref(col_idx)
                raise IntegrityError(f'Result type-metadata pair in column {column} of worksheet {worksheet} is a duplicate')

    def _validate_empty_regions(self):
        # Region above subsamples and left of metadata types

        df_sub = self._df.iloc[self._geometry['metadata_types']['row_idx_slice'], self._geometry['subsamples']['column_idx_slice']]

        if not df_sub.isna().all().all():
            worksheet = f'{self._wb.path.name}::{self._name}'
            raise IntegrityError(f"Region left of metadata types in worksheet {worksheet} is not empty")

    def __iter__(self):
        subsamples_df = self._df.iloc[self._geometry['subsamples']['row_idx_slice'], self._geometry['subsamples']['column_idx_slice']]
        subsamples = list(tuple(x) for x in subsamples_df.values)

        metadata_types = list(self._df.iloc[self._geometry['metadata_types']['row_idx_slice'], self._geometry['metadata_types']['column_idx']])

        result_types_s = self._df.iloc[0, self._geometry['result_types']['column_idx_slice']]
        result_types = list(result_types_s.values)

        metadata_values_lists_df = self._df.iloc[self._geometry['metadata_types']['row_idx_slice'], self._geometry['result_types']['column_idx_slice']]
        metadata_value_lists = list(tuple(x) for x in metadata_values_lists_df.transpose().values)

        results_df = self._df.iloc[self._geometry['subsamples']['row_idx_slice'], self._geometry['result_types']['column_idx_slice']]
        results = list(list(x) for x in results_df.values)

        for y, subsample in enumerate(subsamples):
            sample_col = self._wb.dataset.samples.get_by_name(str(subsample[0]).strip())
            subsample_cols = tuple(str(x).strip() for x in subsample[1:])

            for x, result_type in enumerate(result_types):
                metadata = zip(metadata_types, metadata_value_lists[x])
                metadata = frozenset((t, str(v)) for t, v in metadata if v is not None)

                result_value = str(results[y][x])

                yield Result(sample_col, subsample_cols, result_type, metadata, result_value)
