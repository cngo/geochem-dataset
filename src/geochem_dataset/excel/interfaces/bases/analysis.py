from __future__ import annotations
from abc import ABC

import numpy as np
import pandas as pd

from geochem_dataset.excel.dataclasses import Result
from geochem_dataset.excel.exceptions import IntegrityError
from geochem_dataset.excel.interfaces import xlref, xlrowref, xlcolref

NA_VALUES = ['-1.#IND', '1.#QNAN', '1.#IND', '-1.#QNAN', '#N/A N/A', '#N/A', 'N/A', 'n/a', '<NA>', '#NA', 'NULL', 'null', 'NaN', '-NaN', 'nan', '-nan', '']


class AnalysisExcelWorkbookInterface(ABC):
    def __init__(self, dataset):
        self._dataset = dataset

        self._load()

    def _load(self):
        self._worksheets = {
            sheet_name: AnalysisExcelWorksheetInterface(self, sheet_name)
            for sheet_name in pd.ExcelFile(self.path).sheet_names
        }

        # for sheet_name in pd.ExcelFile(self.path).sheet_names:
        #     self._worksheets[sheet_name] = AnalysisExcelWorksheetInterface(self, sheet_name)

    def _validate(self):
        sheet_names = list(self._worksheets.keys())

        for i, sheet_name in enumerate(sheet_names):
            if i == 0:
                continue

            for result in self._worksheets[sheet_name]:
                for other_sheet_name in sheet_names[:i]:
                    for other_result in self._worksheets[other_sheet_name]:
                        if other_result.sample.name == result.sample.name and \
                                other_result.subsample == result.subsample and \
                                other_result.type == result.type and \
                                other_result.metadata == result.metadata:
                            raise IntegrityError(
                                f"Subsample/result type/metadata combination for result in cell A1 was already used for result in cell A1 of worksheet {other_sheet_name}", workbook=self.path.name, worksheet=sheet_name, cell="A1")

    @property
    def dataset(self):
        return self._dataset

    @property
    def path(self):
        return self._dataset.path / self._name

    def __iter__(self):
        for ws in self._worksheets.values():
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

        - The first two columns must be "SAMPLE" and "SUBSAMPLE" and then followed by zero or more deeper subsample columns.
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

    def __init__(self, workbook: AnalysisExcelWorkbookInterface, sheet_name: str):
        self._workbook = workbook
        self._sheet_name = sheet_name

        self._load_dataframe()
        self._compute_geometry()
        self._validate_dataframe()

    def _load_dataframe(self):
        self._df = pd.read_excel(self._workbook.path, sheet_name=self._sheet_name, header=None, keep_default_na=False, na_values=NA_VALUES)
        self._df = self._df.replace({np.nan: None})

    def _compute_geometry(self):
        self._geometry = {
            'subsamples': {},
            'metadata_types': {},
            'result_types': {},
        }

        self._geometry['subsamples']['columns'] = self._get_geometry_subsamples_columns_slice()
        self._geometry['metadata_types']['column'] = self._get_geometry_metadata_types_column()
        self._geometry['result_types']['columns'] = self._get_geometry_result_types_columns_slice()
        self._geometry['metadata_types']['rows'] = self._get_geometry_metadata_types_rows_slice()
        self._geometry['subsamples']['rows'] = self._get_geometry_subsamples_rows_slice()

    def _get_geometry_subsamples_columns_slice(self):
        # The subsample columns are minimally the first two columns with
        # specific headings. Additional columns have headings prepended with
        # "SUB" again and again.

        first_row = self._df.iloc[0]

        if first_row[0] != 'SAMPLE':
            raise IntegrityError('Cell must be "SAMPLE"', workbook=self._workbook.path.name, worksheet=self._sheet_name, cell="A1")

        if first_row[1] != 'SUBSAMPLE':
            raise IntegrityError('Cell must be "SUBSAMPLE"', workbook=self._workbook.path.name, worksheet=self._sheet_name, cell="B1")

        columns_stop = 2

        for column, heading in first_row.iloc[2:].items():
            expected_heading = 'SUB' + first_row[column - 1]

            if heading != expected_heading:
                break

            columns_stop = columns_stop + 1

        return slice(0, columns_stop)

    def _get_geometry_metadata_types_column(self):
        assert 'subsamples' in self._geometry and 'columns' in self._geometry['subsamples']

        # The metadata types column is expected to be the column following the
        # last subsample column.

        metadata_types_column = self._geometry['subsamples']['columns'].stop

        if metadata_types_column not in self._df.columns or self._df.iloc[0, metadata_types_column] != 'METADATA_TYPE':
            raise IntegrityError('Cell must be "METADATA_TYPE"', workbook=self._workbook.path.name, worksheet=self._sheet_name, cell=xlref(0, metadata_types_column))

        return metadata_types_column

    def _get_geometry_result_types_columns_slice(self):
        assert 'metadata_types' in self._geometry and 'column' in self._geometry['metadata_types']

        # The result type columns are all columns following the metdata types
        # column.

        columns_start = self._geometry['metadata_types']['column'] + 1
        columns_stop = len(self._df.iloc[0])

        return slice(columns_start, columns_stop)

    def _get_geometry_metadata_types_rows_slice(self):
        assert 'metadata_types' in self._geometry and 'column' in self._geometry['metadata_types']

        # The metadata type rows fall between the heading row and the first
        # subsample row.

        s = self._df.iloc[1:, self._geometry['metadata_types']['column']]
        key = s.notnull()
        rows_stop = 1 if s[key].empty else (s[key].index[-1] + 1)

        return slice(1, rows_stop)

    def _get_geometry_subsamples_rows_slice(self):
        assert 'metadata_types' in self._geometry and 'rows' in self._geometry['metadata_types']

        # The subsample rows begin with the row following the last metadata type
        # and end with the last row of the table.

        rows_start = self._geometry['metadata_types']['rows'].stop

        return slice(rows_start, len(self._df))

    def _validate_dataframe(self):
        self._validate_subsamples()
        self._validate_metadata_types()
        self._validate_result_types()
        self._validate_empty_regions()

    def _validate_subsamples(self):
        subsamples_df = self._df.iloc[self._geometry['subsamples']['rows'], self._geometry['subsamples']['columns']]
        samples = [str(x.name).strip() for x in iter(self._workbook.dataset.samples)]

        for row_idx, subsample_s in subsamples_df.iterrows():
            # Check if any subsample fields are not given

            if subsample_s.isna().any():
                worksheet = f'{self._workbook.path.name}::{self._sheet_name}'
                row = xlrowref(row_idx)
                raise IntegrityError(f'Missing value(s) for subsample in row {row} of worksheet {self._workbook.path.name}::{self._sheet_name}')

            # Check if SAMPLE field does not exist in samples file

            sample = str(subsample_s[0]).strip()

            if sample not in samples:
                worksheet = f'{self._workbook.path.name}::{self._sheet_name}'
                cell = xlref(row_idx, 0)
                raise IntegrityError(f'Sample in cell {cell} of worksheet {worksheet} does not exist')

            # Check if subsample is a duplicate

            previous_subsamples_df = self._df.iloc[self._geometry['subsamples']['rows'].start:row_idx, self._geometry['subsamples']['columns']]
            previous_subsamples = [tuple(x) for x in previous_subsamples_df.to_numpy()]

            if tuple(subsample_s) in previous_subsamples:
                worksheet = f'{self._workbook.path.name}::{self._sheet_name}'
                row = xlrowref(row_idx)
                raise IntegrityError(f'Subsample in row {row} of worksheet {worksheet} is a duplicate')

    def _validate_metadata_types(self):
        metadata_types = self._df.iloc[self._geometry['metadata_types']['rows'], self._geometry['metadata_types']['column']]

        for row_idx, metadata_type in metadata_types.items():
            # Check if metadata type is not given

            if metadata_type is None:
                worksheet = f'{self._workbook.path.name}::{self._sheet_name}'
                cell = xlref(row_idx, self._geometry['metadata_types']['column'])
                raise IntegrityError(f'Metadata type is missing in cell {cell} of worksheet {worksheet}')

            # Check if metadata type is a duplicate

            previous_metadata_types = self._df.iloc[self._geometry['metadata_types']['rows'].start:row_idx, self._geometry['metadata_types']['column']]

            if metadata_type in tuple(previous_metadata_types):
                worksheet = f'{self._workbook.path.name}::{self._sheet_name}'
                cell = xlref(row_idx, self._geometry['metadata_types']['column'])
                raise IntegrityError(f'Metadata type in cell {cell} of worksheet {worksheet} is a duplicate')

    def _validate_result_types(self):
        result_types_column_idx_slice = self._geometry['result_types']['columns']
        metadata_types_row_idx_slice = self._geometry['metadata_types']['rows']

        result_type_metadata_df = self._df.iloc[:metadata_types_row_idx_slice.stop, result_types_column_idx_slice]

        for col_idx, result_type_metadata_s in result_type_metadata_df.items():
            # Check if result type is not given

            if result_type_metadata_s[0] is None:
                worksheet = f'{self._workbook.path.name}::{self._sheet_name}'
                cell = xlref(0, col_idx)
                raise IntegrityError(f'Result type in cell {cell} of worksheet {worksheet} is missing')

            # Check if result type / metadata pair is a duplicate

            if result_type_metadata_s.values.tolist() in result_type_metadata_df.loc[:, :col_idx-1].transpose().values.tolist():
                worksheet = f'{self._workbook.path.name}::{self._sheet_name}'
                column = xlcolref(col_idx)
                raise IntegrityError(f'Result type-metadata pair in column {column} of worksheet {worksheet} is a duplicate')

    def _validate_empty_regions(self):
        # Region above subsamples and left of metadata types

        df_sub = self._df.iloc[self._geometry['metadata_types']['rows'], self._geometry['subsamples']['columns']]

        if not df_sub.isna().all().all():
            raise IntegrityError(f"Region left of metadata types is not empty", workbook=self._workbook.path.name, worksheet=self._sheet_name)

    def __iter__(self):
        subsamples_df = self._df.iloc[self._geometry['subsamples']['rows'], self._geometry['subsamples']['columns']]
        subsamples = list(tuple(x) for x in subsamples_df.values)

        metadata_types = list(self._df.iloc[self._geometry['metadata_types']['rows'], self._geometry['metadata_types']['column']])

        result_types_s = self._df.iloc[0, self._geometry['result_types']['columns']]
        result_types = list(result_types_s.values)

        metadata_values_lists_df = self._df.iloc[self._geometry['metadata_types']['rows'], self._geometry['result_types']['columns']]
        metadata_value_lists = list(tuple(x) for x in metadata_values_lists_df.transpose().values)

        results_df = self._df.iloc[self._geometry['subsamples']['rows'], self._geometry['result_types']['columns']]
        results = list(list(x) for x in results_df.values)

        for y, subsample in enumerate(subsamples):
            sample_col = self._workbook.dataset.samples.get_by_name(str(subsample[0]).strip())
            subsample_cols = tuple(str(x).strip() for x in subsample[1:])

            for x, result_type in enumerate(result_types):
                metadata = zip(metadata_types, metadata_value_lists[x])
                metadata = frozenset((t, str(v)) for t, v in metadata if v is not None)

                result_value = str(results[y][x])

                yield Result(sample_col, subsample_cols, result_type, metadata, result_value)
