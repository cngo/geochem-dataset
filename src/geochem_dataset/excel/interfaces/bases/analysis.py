from __future__ import annotations
from abc import ABC
import collections

import numpy as np
import pandas as pd

from geochem_dataset.excel.dataclasses import Result
from geochem_dataset.excel.exceptions import IntegrityError
from geochem_dataset.excel.interfaces import xlref, xlrowref, xlcolref


class AnalysisExcelWorkbookInterface(ABC):
    def __init__(self, dataset):
        self._dataset = dataset
        self._load()

    @property
    def dataset(self):
        return self._dataset

    @property
    def path(self):
        return self._dataset.path / self._name

    @property
    def results(self):
        for ws in self._worksheets.values():
            for result in ws.results:
                yield result

    def _load(self):
        self._worksheets = {
            worksheet_name: AnalysisExcelWorksheetInterface(self, worksheet_name)
            for worksheet_name in pd.ExcelFile(self.path).sheet_names
        }

    # def _validate(self):
    #     sheet_names = list(self._worksheets.keys())

    #     for i, sheet_name in enumerate(sheet_names):
    #         if i == 0:
    #             continue

    #         for result in self._worksheets[sheet_name]:
    #             for other_sheet_name in sheet_names[:i]:
    #                 for other_result in self._worksheets[other_sheet_name]:
    #                     if other_result.sample.name == result.sample.name and \
    #                             other_result.subsample == result.subsample and \
    #                             other_result.type == result.type and \
    #                             other_result.metadata == result.metadata:
    #                         raise IntegrityError(
    #                             f"Subsample/result type/metadata combination for result in cell A1 was already used for result in cell A1 of worksheet {other_sheet_name}", workbook=self.path.name, worksheet=sheet_name, cell="A1")


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

    The following outlines the steps involved in parsing the worksheet:

    1. Load the worksheet into a dataframe and modify it as follows:

        1. Cast values to strings
        2. Strip whitespace from values
        3. Convert empty string values to NaNs
        4. Remove empty rows from the bottom
        5. Remove empty columns from the right

    2. Parse the dataframe:

        1. Parse subsamples:

            1. Determine columns:

                1. A1 and B1 must be "SAMPLE" and "SUBSAMPLE", respectively
                2. Optional subsequent columns, each with a heading equal to the previous heading prefixed with "SUB", e.g. "SUBSUBSAMPLE" for C1

            2. Determine rows:

                1. Begins on first non-empty row
                2. Must end on the last row of the dataframe

            3. For each subsample:

                1. Check if all values are given
                2. Check if sample exists
                3. Check if it's a duplicate of a previous one

        2. Parse metadata types:

            1. Determine column:

                1. Must be the column following the subsample columns

            2. Determine rows (if any):

                1. Must begin on row 2
                2. Must end on row before the first subsample row

            3. For each metadata type:

                1. Check if a value is given
                2. Check if it's a duplicate of a previous one

            4. Check if all cells below the last metadata type are empty

        3. Parse result type/metadata sets:

            1. Determine columns:

                1. Must begin on the column following the metadata type column
                2. Must end on the last column of the dataframe

            2. Determine rows:

                1. Must begin on row 1
                2. Must end on the last metadata type row

            3. For each result type/metadata set:

                1. Check if a value is given for result type
                2. Check if it's a duplicate of a previous one
    """

    def __init__(self, workbook: AnalysisExcelWorkbookInterface, name: str):
        self._workbook = workbook
        self._name = name

        self._load()
        self._parse()

    @property
    def workbook(self) -> AnalysisExcelWorkbookInterface:
        return self._workbook

    @property
    def name(self) -> str:
        return self._name

    @property
    def results(self) -> collections.abc.Generator:
        subsamples = self._df.iloc[
            self._geometry['subsamples']['rows'],
            self._geometry['subsamples']['columns']
        ]

        metadata_types = self._df.iloc[
            self._geometry['metadata_types']['rows'],
            self._geometry['metadata_types']['column']
        ]

        result_type_metadata_sets = self._df.iloc[
            self._geometry['result_type_metadata_sets']['rows'],
            self._geometry['result_type_metadata_sets']['columns']
        ]

        for row_idx, subsample in subsamples.iterrows():
            sample_name = subsample[0]
            subsample_names = subsample[1:]

            for column_idx, result_type_metadata_set_column in result_type_metadata_sets.items():
                # Get result type and metadata

                if isinstance(result_type_metadata_set_column, pd.Series):
                    result_type = result_type_metadata_set_column[0]
                    metadata = result_type_metadata_set_column[1:]
                else:
                    result_type = result_type_metadata_set_column
                    metadata = pd.Series(name=column_idx)

                metadata = dict(
                    (metadata_type, metadata_value)
                    for metadata_type, metadata_value in zip(metadata_types, metadata)
                    if not pd.isna(metadata_value)
                )

                result_value = self._df.loc[row_idx, column_idx]

                if pd.isna(result_value):
                    result_value = None

                yield Result(sample_name, tuple(subsample_names), result_type, metadata, result_value)

    def _load(self):
        self._df = pd.read_excel(self.workbook.path, sheet_name=self.name, header=None, keep_default_na=False)

        self._df = self._df.astype(str)                    # Cast to string
        self._df = self._df.applymap(lambda x: x.strip())  # Strip whitespace
        self._df = self._df.replace('', np.nan)            # Replace empty strings with NaN

        # Drop all empty rows from the end of the dataframe
        last_non_empty_row_idx = self._df.notna().any(axis=1).drop_duplicates(keep='last').index[0]
        self._df = self._df.loc[:last_non_empty_row_idx]

        # Drop all empty columns from the end of the dataframe
        last_non_empty_column_idx = self._df.notna().any(axis=0).drop_duplicates(keep='last').index[0]
        self._df = self._df.loc[:, :last_non_empty_column_idx]

    def _parse(self):
        self._geometry = {
            'subsamples': {},
            'metadata_types': {},
            'result_type_metadata_sets': {},
        }

        self._parse_01_subsamples()
        self._parse_02_metadata_types()
        self._parse_03_result_type_metadata_sets()

    def _parse_01_subsamples(self):
        first_row = self._df.iloc[0]

        # ERROR if mandatory headings missing

        if first_row[0] != 'SAMPLE':
            raise IntegrityError('Cell A1 must be "SAMPLE"', workbook=self.workbook.path.name, worksheet=self.name)

        if len(first_row) < 2 or first_row[1] != 'SUBSAMPLE':
            raise IntegrityError('Cell B1 must be "SUBSAMPLE"', workbook=self.workbook.path.name, worksheet=self.name)

        # COMPUTE COLUMNS GEOMETRY

        # Find additional subsample columns

        subsample_columns_idx_stop = 2

        for column_idx, heading in first_row.iloc[subsample_columns_idx_stop:].items():
            expected_subsample_heading = 'SUB' + first_row[column_idx - 1]

            if heading != expected_subsample_heading:
                break

            subsample_columns_idx_stop += 1

        self._geometry['subsamples']['columns'] = slice(0, subsample_columns_idx_stop)

        # COMPUTE ROWS GEOMETRY

        # Find first subsample row with a non-null value
        rows_start_idx = self._df.iloc[1:, self._geometry['subsamples']['columns']]. \
            notna(). \
            any(axis=1). \
            replace(False, np.nan). \
            first_valid_index()

        rows_stop_idx = self._df.index[-1] + 1

        self._geometry['subsamples']['rows'] = (
            slice(rows_start_idx, self._df.index[-1] + 1)  # From 1st subsample row (one with any non-null value) to last row of entire worksheet (one with any non-null value)
            if rows_start_idx else
            slice(rows_stop_idx, rows_stop_idx)  # Empty slice that doesn't overlap any metadata type rows
        )

        # VALIDATE ROWS

        sample_names = [str(x.name).strip() for x in iter(self.workbook.dataset.samples)]  # Used to check if SAMPLE names used actually exist
        rows = self._df.iloc[self._geometry['subsamples']['rows'], self._geometry['subsamples']['columns']]

        for row_idx, row in rows.iterrows():
            # ERROR if missing values for subsample

            if row.isnull().any():
                row_xl_idx = xlrowref(row_idx)
                raise IntegrityError(f'Missing value(s) for subsample on row {row_xl_idx}', workbook=self.workbook.path.name, worksheet=self.name)

            # ERROR if subsample is a duplicate

            duplicate_of_row_idx = None
            previous_rows = rows.loc[:row_idx-1]

            for previous_row_idx, previous_row in previous_rows.iterrows():
                if tuple(row) == tuple(previous_row):
                    duplicate_of_row_idx = previous_row_idx
                    break

            if duplicate_of_row_idx:
                row_xl_idx = xlrowref(row_idx)
                duplicate_of_row_xl_idx = xlrowref(duplicate_of_row_idx)
                raise IntegrityError(f'Subsample on row {row_xl_idx} is a duplicate of subsample on row {duplicate_of_row_xl_idx}', workbook=self.workbook.path.name, worksheet=self.name)

            sample_name = row[0]

            if sample_name not in sample_names:
                row_xl_idx = xlrowref(row_idx)
                raise IntegrityError(f'Sample value "{sample_name}" of subsample on row {row_xl_idx} does not exist in "SAMPLES.xlsx"', workbook=self.workbook.path.name, worksheet=self.name)

    def _parse_02_metadata_types(self):
        # SAVE GEOMETRY (depends entirely on subsamples geometry)

        self._geometry['metadata_types']['column'] = self._geometry['subsamples']['columns'].stop
        self._geometry['metadata_types']['rows'] = slice(1, self._geometry['subsamples']['rows'].start)

        # GET metadata type column (including heading) (if one exists)

        column = (
            self._df.iloc[:, self._geometry['metadata_types']['column']]
            if self._geometry['metadata_types']['column'] in self._df.columns
            else None
        )

        # ERROR if mandatory heading is missing

        if column is None or column[0] != 'METADATA_TYPE':
            cell_xl_idx = xlref(0, self._geometry['metadata_types']['column'])
            raise IntegrityError(f'Cell {cell_xl_idx} must be "METADATA_TYPE"', workbook=self.workbook.path.name, worksheet=self.name)

        # VALIDATE metadata types falling in geometry

        rows = column[self._geometry['metadata_types']['rows']]

        for row_idx, metadata_type in rows.items():
            # ERROR if a metadata type was not given

            if metadata_type is None:
                row_xl_idx = xlrowref(row_idx)
                raise IntegrityError(f'Metadata type missing from row {row_xl_idx}', workbook=self.workbook.path.name, worksheet=self.name)

            # ERROR if metadata type is a duplicate of a previous one

            duplicate_of_row_idx = None
            previous_rows = rows.loc[:row_idx-1]

            for previous_row_idx, previous_metadata_type in previous_rows.items():
                if metadata_type == previous_metadata_type:
                    duplicate_of_row_idx = previous_row_idx
                    break

            if duplicate_of_row_idx:
                row_xl_idx = xlrowref(row_idx)
                duplicate_of_row_xl_idx = xlrowref(duplicate_of_row_idx)
                raise IntegrityError(f'Metadata type on row {row_xl_idx} is a duplicate of metadata type on row {duplicate_of_row_xl_idx}', workbook=self.workbook.path.name, worksheet=self.name)

        # ERROR if any cells below last metadata type are not empty

        rows = column[self._geometry['metadata_types']['rows'].stop:]
        rows = rows[rows.notnull()]

        if len(rows) > 0:
            cell_xl_idx = xlref(rows.index[0], self._geometry['metadata_types']['column'])
            raise IntegrityError(f'Metadata type in cell {cell_xl_idx} cannot be given because a subsample exists on the same row', workbook=self.workbook.path.name, worksheet=self.name)

    def _parse_03_result_type_metadata_sets(self):
        # Save expected geometry (depends on metadata types geometry)

        self._geometry['result_type_metadata_sets']['rows'] = slice(0, self._geometry['metadata_types']['rows'].stop)
        self._geometry['result_type_metadata_sets']['columns'] = slice(self._geometry['metadata_types']['column'] + 1, len(self._df.columns))

        # Validate dataframe of result type/metdata sets

        df = self._df.iloc[self._geometry['result_type_metadata_sets']['rows'], self._geometry['result_type_metadata_sets']['columns']]

        for column_idx, column in df.items():
            # EXTRACT result type and metadata from column

            if isinstance(column, pd.Series):
                result_type = column[0]
                metadata = tuple(column[1:])
            else:
                result_type = column
                metadata = tuple()

            # ERROR if result type not given

            if len(result_type) == 0:
                column_xl_idx = xlcolref(column_idx)
                raise IntegrityError(f'Result type is missing on column {column_xl_idx}', workbook=self.workbook.path.name, worksheet=self.name)

            # ERROR if duplicate result type/metadata set

            duplicate_of_column_idx = None
            previous_df = df.loc[0, :column_idx-1]

            for previous_column_idx, previous_column in previous_df.items():
                if isinstance(previous_column, pd.Series):
                    previous_result_type = previous_column[0]
                    previous_metadata = tuple(previous_column[1:])
                else:
                    previous_result_type = previous_column
                    previous_metadata = tuple()

                if result_type == previous_result_type and metadata == previous_metadata:
                    duplicate_of_column_idx = previous_column_idx
                    break

            if duplicate_of_column_idx:
                column_xl_idx = xlcolref(column_idx)
                duplicate_of_column_xl_idx = xlcolref(duplicate_of_column_idx)
                raise IntegrityError(f'Result type/metadata set on column {column_xl_idx} is a duplicate of one on column {duplicate_of_column_xl_idx}', workbook=self.workbook.path.name, worksheet=self.name)
