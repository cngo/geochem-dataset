from __future__ import annotations
import abc
from collections.abc import Generator
import itertools
import logging

import numpy as np
import pandas as pd
from tqdm import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm

from . import dataset, errors, models, utils
from .utils import Workbook


## ---------------------------------------------------------------------------------------------------------------------
## Dataset workbook
## ---------------------------------------------------------------------------------------------------------------------


class DatasetWorkbook(Workbook, abc.ABC):
    def __init__(self, dataset: dataset.Dataset, **kwargs) -> None:
        self.dataset = dataset
        super().__init__(self.dataset.path / self._meta.workbook_name, **kwargs)

    def __iter__(self):
        return self.iter_objects()

    @property
    @abc.abstractmethod
    def _meta(self) -> utils.Meta:
        pass

    @abc.abstractmethod
    def iter_objects(self) -> Generator:
        pass


class BasicDatasetWorkbook(DatasetWorkbook):
    """An abstract interface for reading an Excel file with one worksheet and a simple table structure: first row are
    headings and subsequent rows are data.

    The interface provides simple validation: expected sheet name, expected column names, unique constraints, foreign
    key constraints, min/max data rows.

    """

    def __init__(self, dataset: dataset.Dataset, **kwargs) -> None:
        super().__init__(dataset, **kwargs)

        self._parse_data()
        self._validate()

    @property
    def worksheet(self):
        return self.worksheets[self._meta.worksheet_name]

    def _parse_data(self):
        self._create_indexes()

    def _create_indexes(self):
        wb_name            = self._meta.workbook_name
        ws_name            = self._meta.worksheet_name
        unique_constraints = self._meta.unique_constraints

        ws = self.worksheets[self._meta.worksheet_name]

        column_indices = {col_name: col_idx for col_idx, col_name in enumerate(ws.data[0])}

        self._indexes = {}

        for constraint_columns in unique_constraints:
            constraint_columns = tuple(constraint_columns)
            self._indexes[constraint_columns] = index = {}

            for row_idx, row in enumerate(ws.data[1:], 1):
                row_key = tuple(row[column_indices[x]] for x in constraint_columns)

                if other_row_idx := index.get(row_key):
                    message = f"Row {row_idx} violates unique constraint on columns: {constraint_columns} (duplicate of row {other_row_idx})"
                    raise errors.IntegrityError(message, dataset=self.dataset.name, workbook=wb_name, worksheet=ws_name)

                index[row_key] = row_idx

    def _validate(self):
        self._validate_column_headings()
        self._validate_counts()
        self._validate_foreign_key_constraints()

    def _validate_column_headings(self):
        """Validate the column headings of the worksheet

        Checks for missing headings and, optionally, extra headings.
        """
        ds = self.dataset
        wb = self
        ws = self.worksheet

        given_columns = set(ws.data[0])
        expected_columns = set(self._meta.columns)

        if (missing_heading_column_indexes := [i for i, h in enumerate(ws.data[0]) if h == None]):
            raise errors.MissingHeadingsError(ds=ds, wb=wb, ws=ws, column_indexes=missing_heading_column_indexes)

        if (missing_columns := expected_columns - given_columns):
            missing_columns = list(sorted(missing_columns))
            raise errors.MissingColumnsError(ds=ds, wb=wb, ws=ws, columns=missing_columns)

        if not ds.extra_columns_ok:
            if (extra_columns := given_columns - expected_columns):
                extra_columns = list(sorted(extra_columns))
                raise errors.ExtraColumnsError(ds=ds, wb=wb, ws=ws, columns=extra_columns)

    def _validate_counts(self):
        wb_name  = self._meta.workbook_name
        ws_name  = self._meta.worksheet_name
        min_rows = self._meta.min_rows
        max_rows = self._meta.max_rows

        row_count = self.count

        if min_rows and row_count < min_rows:
            max_rows_str = ("unlimited" if max_rows is None else str(max_rows))
            message      = f"Too few rows: {row_count} (min is {min_rows} and max is {max_rows_str})"
            raise errors.IntegrityError(message, workbook=wb_name, worksheet=ws_name)

        if max_rows and row_count > max_rows:
            max_rows_str = ("unlimited" if max_rows is None else str(max_rows))
            message      = f"Too many rows: {row_count} (min is {min_rows} and max is {max_rows_str})"
            raise errors.IntegrityError(message, workbook=wb_name, worksheet=ws_name)

    def _validate_foreign_key_constraints(self):
        wb_name        = self._meta.workbook_name
        ws_name        = self._meta.worksheet_name
        fk_constraints = self._meta.foreign_key_constraints

        if not fk_constraints:
            return

        column_indices = {col_name: col_idx for col_idx, col_name in enumerate(self.worksheet.data[0])}

        for row_idx, row in enumerate(self.worksheet.data[1:], 1):
            for fk_column_names, dataset_fk_interface_attr, fk_index_key in fk_constraints:
                fk_value             = tuple(row[column_indices[x]] for x in fk_column_names)
                dataset_fk_interface = getattr(self.dataset, dataset_fk_interface_attr)
                fk_index             = dataset_fk_interface._indexes[fk_index_key]

                if fk_value not in fk_index:
                    message = f"Row {row_idx} violates foreign key constraint on columns: {fk_column_names}"
                    raise errors.IntegrityError(message, workbook_name=wb_name, worksheet_name=ws_name)

    def iter_objects(self):
        required_column_names = self._meta.columns
        fk_constraints        = self._meta.foreign_key_constraints
        model_class           = self._meta.model
        model_field_map       = getattr(self._meta, "model_field_map", None)
        ws                    = self.worksheets[self._meta.worksheet_name]

        column_names       = ws.data[0]
        extra_column_names = tuple(set(column_names) - set(required_column_names))

        for row_idx, row in enumerate(ws.data[1:], 1):
            row = dict(zip(column_names, row))  # convert row to dict

            # Replace FK columns with row idx columns
            for fk_column_names, fk_iface_attr, fk_iface_index_key in fk_constraints:
                fk_value   = tuple(row[n] for n in fk_column_names)
                fk_iface   = getattr(self.dataset, fk_iface_attr)
                fk_row_idx = fk_iface.indexes[fk_iface_index_key][fk_value]

                for n in fk_column_names:
                    del row[n]

                fk_row_idx_column_name      = f"{fk_iface_attr.upper()}_ROW_IDX"
                row[fk_row_idx_column_name] = fk_row_idx

            kwargs = row.copy()
            extra = { n: str(kwargs.pop(n)) for n in extra_column_names }

            if model_field_map:
                for from_, to_ in model_field_map:
                    kwargs[to_] = kwargs[from_]
                    del kwargs[from_]

            kwargs = { n.lower(): v for n, v in kwargs.items() }
            kwargs["row_idx"] = row_idx
            extra = { n.lower(): v for n, v in extra.items() }

            yield model_class(**kwargs, extra=extra)

    def get_by_row_idx(self, row_idx: int):
        required_column_names = self._meta.columns
        fk_constraints        = self._meta.foreign_key_constraints
        model_class           = self._meta.model
        model_field_map       = getattr(self._meta, "model_field_map", None)
        ws                    = self.worksheets[self._meta.worksheet_name]

        column_names       = ws.data[0]
        extra_column_names = tuple(set(column_names) - set(required_column_names))

        row = ws.data[row_idx]
        row = dict(zip(column_names, row))  # convert row to dict

        # Replace FK columns with row idx columns
        for fk_column_names, fk_iface_attr, fk_iface_index_key in fk_constraints:
            fk_value   = tuple(row[n] for n in fk_column_names)
            fk_iface   = getattr(self.dataset, fk_iface_attr)
            fk_row_idx = fk_iface.indexes[fk_iface_index_key][fk_value]

            for n in fk_column_names:
                del row[n]

            fk_row_idx_column_name      = f"{fk_iface_attr.upper()}_ROW_IDX"
            row[fk_row_idx_column_name] = fk_row_idx

        kwargs = row.copy()
        extra = { n: str(kwargs.pop(n)) for n in extra_column_names }

        if model_field_map:
            for from_, to_ in model_field_map:
                kwargs[to_] = kwargs[from_]
                del kwargs[from_]

        kwargs = { n.lower(): v for n, v in kwargs.items() }
        kwargs["row_idx"] = row_idx
        extra = { n.lower(): v for n, v in extra.items() }

        return model_class(**kwargs, extra=extra)

    @property
    def indexes(self) -> dict[tuple[str, ...], int]:
        return self._indexes  # TODO: Ensure unmutable value returned

    @property
    def count(self) -> int:
        """Return the number of items in the workbook.
        """
        return len(self.worksheet.data[1:])


class AnalysisDatasetWorkbook(DatasetWorkbook):
    def __init__(self, dataset: dataset.Dataset, **kwargs) -> None:
        kwargs["worksheet_class"] = AnalysisDatasetWorksheet
        super().__init__(dataset, **kwargs)
        self._parse_data()

    def _parse_data(self) -> None:
        for ws in self.worksheets.values():
            ws.parse_data()

        self._check_duplicates()

    def _check_duplicates(self):
        worksheets = list(self.worksheets.values())

        for ws_i, ws in enumerate(worksheets):
            if ws_i == 0:
                continue

            ws_subsamples_index                = ws._indexes['subsamples']
            ws_result_type_metadata_sets_index = ws._indexes['result_type_metadata_sets']

            previous_worksheets = worksheets[:ws_i]

            for previous_ws in previous_worksheets:
                previous_ws_subsamples_index                = previous_ws._indexes['subsamples']
                previous_ws_result_type_metadata_sets_index = previous_ws._indexes['result_type_metadata_sets']

                common_ws_subsamples               = set(ws_subsamples_index.keys()) & set(previous_ws_subsamples_index.keys())
                common_ws_result_type_metdata_sets = set(ws_result_type_metadata_sets_index.keys()) & set(previous_ws_result_type_metadata_sets_index.keys())

                if common_ws_subsamples and common_ws_result_type_metdata_sets:
                    ws_subsample_row_idxes                = sorted(ws_subsamples_index[x] for x in common_ws_subsamples)
                    ws_result_type_metadata_set_col_idxes = sorted(ws_result_type_metadata_sets_index[x] for x in common_ws_result_type_metdata_sets)

                    previous_ws_subsample_row_idxes                = sorted(previous_ws_subsamples_index[x] for x in common_ws_subsamples)
                    previous_ws_result_type_metadata_set_col_idxes = sorted(previous_ws_result_type_metadata_sets_index[x] for x in common_ws_result_type_metdata_sets)

                    cells       = [utils.xlref(ri, ci) for ri, ci in itertools.product(ws_subsample_row_idxes, ws_result_type_metadata_set_col_idxes)]
                    other_cells = [utils.xlref(ri, ci) for ri, ci in itertools.product(previous_ws_subsample_row_idxes, previous_ws_result_type_metadata_set_col_idxes)]

                    raise errors.DuplicateAnalysisResultParametersError(
                        dataset=self.dataset.name,
                        workbook=self.path.name,
                        worksheet=ws.name,
                        cells=cells,
                        other_worksheet=previous_ws.name,
                        other_cells=other_cells,
                    )

    def iter_objects(self):
        return super().iter_objects()

    ##----------------------------------------------------------------------------------------------
    ## Count methods
    ##----------------------------------------------------------------------------------------------

    @property
    def subsample_count(self) -> int:
        return sum(ws.subsample_count for ws in self.worksheets.values())

    @property
    def result_type_count(self) -> int:
        return sum(ws.result_type_count for ws in self.worksheets.values())

    @property
    def metadata_type_count(self) -> int:
        return sum(ws.metadata_type_count for ws in self.worksheets.values())

    @property
    def metadata_set_count(self) -> int:
        return sum(ws.metadata_set_count for ws in self.worksheets.values())

    @property
    def result_count(self) -> int:
        return sum(ws.result_count for ws in self.worksheets.values())

    ##----------------------------------------------------------------------------------------------
    ## Item generator methods
    ##----------------------------------------------------------------------------------------------

    @property
    def subsamples(self) -> Generator[tuple, None, None]:
        for ws_data in self.worksheets.values():
            for subsample in ws_data.subsamples:
                yield subsample

    @property
    def result_types(self) -> Generator[str, None, None]:
        for ws in self.worksheets.values():
            for result_type in ws.result_types:
                yield result_type

    @property
    def metadata_types(self) -> Generator[str, None, None]:
        for ws in self.worksheets.values():
            for metadata_type in ws.metadata_types:
                yield metadata_type

    @property
    def metadata_sets(self) -> Generator[str, None, None]:
        for ws in self.worksheets.values():
            for metadata_set in ws.metadata_sets:
                yield metadata_set

    @property
    def results(self) -> Generator[models.Result, None, None]:
        for ws in self.worksheets.values():
            for result in ws.results:
                yield result


class AnalysisDatasetWorksheet(utils.Worksheet):
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
    def parse_data(self):
        self._normalize_data()
        self._compute_geometry()

        self._indexes = {
            "subsamples": {},
            "metadata_types": {},
            "result_type_metadata_sets": {},
        }

        self._process_subsamples()
        self._process_metadata_types()
        self._process_result_types_and_metadata_sets()
        self._check_empty_regions()

    def _normalize_data(self):
        for row_idx, row in enumerate(self.data):
            for col_idx, value in enumerate(row):
                if value is None:
                    continue

                # Cast values to string and strip whitespace
                new_value = str(value).strip()

                # Convert to NaN if string is empty
                if new_value == "":
                    new_value = np.nan

                self.data[row_idx][col_idx] = new_value

    def _compute_geometry(self):
        self._geometry = utils.Meta(
            subsamples     = {},
            metadata_types = {},
            result_types   = {},
            metadata_sets  = {},
            results        = {},
        )

        ## Subsamples geometry
        subsample_columns_idx_stop = 2
        for column_idx, heading in enumerate(self.data[0][subsample_columns_idx_stop:]):
            expected_subsample_heading = 'SUB' + self.data[0][column_idx - 1]
            if heading != expected_subsample_heading:
                break
            subsample_columns_idx_stop += 1
        self._geometry.subsamples['columns'] = slice(0, subsample_columns_idx_stop)
        for row_idx, row in enumerate(self.data[1:], 1):
            if any(row[self._geometry.subsamples['columns']]):
                break
        subsample_rows_start_idx = row_idx
        subsample_rows_stop_idx = len(self.data)
        self._geometry.subsamples['rows'] = (
            slice(subsample_rows_start_idx, subsample_rows_stop_idx)
            if subsample_rows_start_idx else
            slice(subsample_rows_stop_idx, subsample_rows_stop_idx)
        )

        ## Metadata types geometry
        ## NOTE: Geometry dependencies: subsamples
        self._geometry.metadata_types['rows'] = slice(1, self._geometry.subsamples['rows'].start)
        self._geometry.metadata_types['column'] = self._geometry.subsamples['columns'].stop

        ## Result types geometry
        ## NOTE: Geometry dependencies: metadata types
        self._geometry.result_types['row'] = 0
        self._geometry.result_types['columns'] = \
            slice(self._geometry.metadata_types['column'] + 1, len(self.data[0]))

        ## Metadata sets geometry
        ## NOTE: Geometry dependencies: metadata types
        self._geometry.metadata_sets['rows'] = self._geometry.metadata_types['rows']
        self._geometry.metadata_sets['columns'] = \
            slice(self._geometry.metadata_types['column'] + 1, len(self.data[0]))

        ## Metadata sets geometry
        ## NOTE: Geometry dependencies: subsamples, result types
        self._geometry.results['rows'] = self._geometry.subsamples['rows']
        self._geometry.results['columns'] = self._geometry.result_types['columns']

    def _process_subsamples(self):
        index = self._indexes["subsamples"]

        ## -------------------------------------------------------------------------------------------------------------
        ## Validate headings
        ## -------------------------------------------------------------------------------------------------------------

        first_row = self.data[0]

        if first_row[0] != 'SAMPLE':
            raise errors.IntegrityError("Cell A1 must be SAMPLE", workbook=self.workbook.path.name, worksheet=self.name)

        if len(first_row) < 2 or first_row[1] != "SUBSAMPLE":
            raise errors.IntegrityError("Cell B1 must be SUBSAMPLE", workbook=self.workbook.path.name, worksheet=self.name)

        ## -------------------------------------------------------------------------------------------------------------
        ## Validate values
        ## -------------------------------------------------------------------------------------------------------------

        subsample_row_slice     = self._geometry.subsamples['rows']
        subsample_columns_slice = self._geometry.subsamples['columns']

        for row_idx, row in enumerate(self.data[subsample_row_slice], subsample_row_slice.start):
            # check if all values are given for subsample
            for col_idx, value in enumerate(row[subsample_columns_slice]):
                if value is None:
                    column_name = self.data[0][col_idx]
                    row_xl_idx = utils.xlrowref(row_idx)
                    message = f"Empty value for column {column_name} of row {row_xl_idx}"
                    raise errors.IntegrityError(message, dataset=self.workbook.dataset.name, workbook=self.workbook.path.name, worksheet=self.name)

            # check if value for SAMPLE exists
            sample_name = row[0]
            if self.workbook.dataset.samples.get_by_name(sample_name) is None:
                column_name = self.data[0][0]
                row_xl_idx = utils.xlrowref(row_idx)
                message = f"Value for column {column_name} of row {row_xl_idx} does not exist in SAMPLES.xlsx"
                raise errors.IntegrityError(message, dataset=self.workbook.dataset.name, workbook=self.workbook.path.name, worksheet=self.name)

            # check if subsample is unique within worksheet
            row_key = tuple(row[subsample_columns_slice])
            if other_row_idx := index.get(row_key):
                column_names = tuple(self.data[0][subsample_columns_slice])
                message = f"Row {row_idx} violates unique constraint on columns: {column_names} (duplicate of row {other_row_idx})"
                raise errors.IntegrityError(message, dataset=self.workbook.dataset.name, workbook=self.workbook.path.name, worksheet=self.name)

            # add subsample to index
            index[row_key] = row_idx

    def _process_metadata_types(self):
        index = self._indexes["metadata_types"]

        metadata_types_col_idx    = self._geometry.metadata_types['column']
        metadata_types_rows_slice = self._geometry.metadata_types['rows']

        ## -------------------------------------------------------------------------------------------------------------
        ## Validate headings
        ## -------------------------------------------------------------------------------------------------------------

        metadata_types_heading = "METADATA_TYPE"

        if self.data[0][metadata_types_col_idx] != metadata_types_heading:
            cell_xl_idx = utils.xlref(0, metadata_types_col_idx)
            message     = f"Cell {cell_xl_idx} must be {metadata_types_heading}"
            raise errors.IntegrityError(message, workbook=self.workbook.path.name, worksheet=self.name)

        ## -------------------------------------------------------------------------------------------------------------
        ## Validate values
        ## -------------------------------------------------------------------------------------------------------------

        for row_idx, row in enumerate(self.data[metadata_types_rows_slice], metadata_types_rows_slice.start):
            metadata_type = row[metadata_types_col_idx]

            # check that metadata type is given
            if metadata_type is None:
                row_xl_idx = utils.xlrowref(row_idx)
                message    = f"Empty value for column {metadata_types_heading} on row {row_xl_idx}"
                raise errors.IntegrityError(message, workbook=self.workbook.path.name, worksheet=self.name)

            # check if metadata type is unique within worksheet
            if other_row_idx := index.get(metadata_type):
                row_xl_idx = utils.xlrowref(row_idx)
                message = f"Metadata type \"{metadata_type}\" on row {row_xl_idx} is not unique (duplicate of row {other_row_idx})"
                raise errors.IntegrityError(message, dataset=self.dataset.name, workbook=self.workbook.path.name, worksheet=self.name)

            # add metadata type to index
            index[metadata_type] = row_idx

    def _process_result_types_and_metadata_sets(self):
        index = self._indexes["result_type_metadata_sets"]

        result_types_row_idx        = self._geometry.result_types['row']
        result_types_columns_slice  = self._geometry.result_types['columns']

        metadata_sets_row_slice     = self._geometry.metadata_sets['rows']
        metadata_sets_columns_slice = self._geometry.metadata_sets['columns']

        result_type_metadata_set_pairs_row_slice = slice(result_types_row_idx, metadata_sets_row_slice.stop)
        result_type_metadata_set_pairs_column_slice = result_types_columns_slice

        ## -------------------------------------------------------------------------------------------------------------
        ## Validate values
        ## -------------------------------------------------------------------------------------------------------------

        for col_idx, result_type_metadata_set in enumerate(self.data.T[result_type_metadata_set_pairs_column_slice, result_type_metadata_set_pairs_row_slice], result_type_metadata_set_pairs_column_slice.start):
            result_type = result_type_metadata_set[0]
            metadata_values = result_type_metadata_set[1:]
            metadata_set = tuple(sorted((x for x in zip(self.metadata_types, metadata_values)), key=lambda x: x[0]))
            result_type_metadata_set = (result_type, metadata_set)

            # check that result type is given
            if result_type is None:
                cell_xl_idx = utils.xlref(col_idx, result_type_metadata_set_pairs_row_slice.start)
                message     = f"Empty value for result type in cell {cell_xl_idx}"
                raise errors.IntegrityError(message, workbook=self.workbook.path.name, worksheet=self.name)

            # check if metadata set is unique within worksheet
            if other_col_idx := index.get(result_type_metadata_set):
                col_xl_idx = utils.xlcolref(col_idx)
                message    = f"Result type and metadata set of column {col_xl_idx} is not unique (duplicate of column {other_col_idx})"
                raise errors.IntegrityError(message, dataset=self.dataset.name, workbook=self.workbook.path.name, worksheet=self.name)

            # add result type and metadata set to index
            index[result_type_metadata_set] = col_idx

    def _check_empty_regions(self):
        # TODO: Complete this

        # ERROR if any cells below last metadata type are not empty

        # rows = column[self._geometry.metadata_types['rows'].stop:]
        # rows = rows[rows.notnull()]

        # if len(rows) > 0:
        #     cell_xl_idx = utils.xlref(rows.index[0], self._geometry.metadata_types['column'])
        #     raise errors.IntegrityError(f'Cell {cell_xl_idx} is expected to be empty; a subsample exists on the same row', workbook=self.workbook.path.name, worksheet=self.name)
        pass

    ##----------------------------------------------------------------------------------------------
    ## Count methods
    ##----------------------------------------------------------------------------------------------

    @property
    def subsample_count(self) -> int:
        _slice = self._geometry.subsamples['rows']
        return _slice.stop - _slice.start

    @property
    def metadata_type_count(self) -> int:
        _slice = self._geometry.metadata_types['rows']
        return _slice.stop - _slice.start

    @property
    def result_type_count(self) -> int:
        _slice = self._geometry.result_types['columns']
        return _slice.stop - _slice.start

    @property
    def metadata_set_count(self) -> int:
        return self.result_type_count

    @property
    def result_count(self) -> int:
        return self.subsample_count * self.result_type_count

    ## -----------------------------------------------------------------------------------------------------------------
    ## Item iterator methods
    ## -----------------------------------------------------------------------------------------------------------------

    @property
    def subsamples(self) -> Generator[tuple[str, ...], None, None]:
        row_slice = self._geometry.subsamples['rows']
        col_slice = self._geometry.subsamples['columns']

        for row_idx in range(row_slice.start, row_slice.stop):
            yield tuple(self.data[row_idx][col_slice])

    @property
    def result_types(self) -> Generator[str, None, None]:
        row_idx   = self._geometry.result_types['row']
        column_slice = self._geometry.result_types['columns']

        for col_idx in range(column_slice.start, column_slice.stop):
            yield self.data[row_idx][col_idx]

    @property
    def metadata_types(self) -> Generator[str, None, None]:
        row_slice = self._geometry.metadata_types['rows']
        col_idx   = self._geometry.metadata_types['column']

        for row_idx in range(row_slice.start, row_slice.stop):
            yield self.data[row_idx][col_idx]

    @property
    def metadata_sets(self) -> Generator[tuple[str, str], None, None]:
        row_slice = self._geometry.metadata_sets['rows']
        col_slice = self._geometry.metadata_sets['columns']

        data_T = self.data.T

        for column_idx in range(col_slice.start, col_slice.stop):
            metadata_values = data_T[column_idx][row_slice]
            yield tuple(sorted((x for x in zip(self.metadata_types, metadata_values)), key=lambda x: x[0]))

    @property
    def results(self) -> Generator[models.Result, None, None]:
        result_rows_slice = self._geometry.results['rows']
        result_cols_slice = self._geometry.results['columns']
        subsample_cols_slice = self._geometry.subsamples['columns']
        result_type_row_idx = self._geometry.result_types['row']
        metadata_set_rows_slice = self._geometry.metadata_sets['rows']

        metadata_types = list(self.metadata_types)

        data_T = self.data.T

        for result_row_idx in range(result_rows_slice.start, result_rows_slice.stop):
            # sample, subsample
            subsample = tuple(self.data[result_row_idx][subsample_cols_slice])
            sample_name = subsample[0]
            sample = self.workbook.dataset.samples.get_by_name(sample_name)
            subsample_parts = tuple(subsample[1:])

            for result_col_idx in range(result_cols_slice.start, result_cols_slice.stop):
                # worksheet
                worksheet = self.name

                # cell
                cell = utils.xlref(result_row_idx, result_col_idx)

                # result type
                result_type = self.data[result_type_row_idx][result_col_idx]

                # metadata set
                metadata_values = data_T[result_col_idx][metadata_set_rows_slice]
                metadata_set = tuple(sorted((x for x in zip(self.metadata_types, metadata_values)), key=lambda x: x[0]))

                # value
                value = self.data[result_row_idx][result_col_idx]
                if pd.isna(value):
                    value = ''

                yield models.Result(worksheet, cell, sample.row_idx, subsample_parts, result_type, metadata_set, value)


## ---------------------------------------------------------------------------------------------------------------------
## Workbook interfaces
## ---------------------------------------------------------------------------------------------------------------------


class DocumentsInterface(BasicDatasetWorkbook):
    _meta = utils.Meta(
        workbook_name  = 'DOCUMENT.xlsx',
        worksheet_name = 'DOCUMENT',
        columns = (
            'RECOMMENDED_CITATION',
        ),
        unique_constraints = [
            ('RECOMMENDED_CITATION',)
        ],
        foreign_key_constraints = [],
        min_rows                = 1,
        max_rows                = 1,
        model                   = models.Document,
        model_field_map         = None
    )

    def get_by_recommended_citation(self, recommended_citation):
        return self.get_by(recommended_citation=recommended_citation)


class SurveysInterface(BasicDatasetWorkbook):
    _meta = utils.Meta(
        workbook_name  = 'SURVEYS.xlsx',
        worksheet_name = 'SURVEYS',
        columns = (
            'TITLE',
            'ORGANIZATION',
            'YEAR_BEGIN',
            'YEAR_END',
            'PARTY_LEADER',
            'DESCRIPTION',
            'GSC_CATALOG_NUMBER',
        ),
        unique_constraints = [
            ('TITLE',)
        ],
        foreign_key_constraints = [],
        min_rows                = 1,
        max_rows                = None,
        model                   = models.Survey,
    )

    def get_by_title(self, title):
        return self.get_by(title=title)


class SamplesInterface(BasicDatasetWorkbook):
    _meta = utils.Meta(
        workbook_name  = 'SAMPLES.xlsx',
        worksheet_name = 'SAMPLES',
        columns = (
            "SURVEY_TITLE",
            "STATION",
            "EARTHMAT",
            "SAMPLE",
            "LAT_NAD27",
            "LONG_NAD27",
            "LAT_NAD83",
            "LONG_NAD83",
            "X_NAD27",
            "Y_NAD27",
            "X_NAD83",
            "Y_NAD83",
            "ZONE",
            "EARTHMAT_TYPE",
            "STATUS",
        ),
        unique_constraints = [
            ('SURVEY_TITLE', 'STATION', 'EARTHMAT', 'SAMPLE'),
        ],
        foreign_key_constraints = [
            # fk_column_names, fk_dataset_interface_attr, fk_dataset_interface_index_key
            (('SURVEY_TITLE',), 'surveys', ('TITLE',)),
        ],
        min_rows        = 1,
        max_rows        = None,
        model           = models.Sample,
        model_field_map = (
            ('SAMPLE', 'name'),
        ),

        # fields = [
        #     # (excel_column, model_field)
        #     ("SURVEY_TITLE",  "survey"),
        #     ("STATION",       "station"),
        #     ("EARTHMAT",      "earthmat"),
        #     ("SAMPLE",        "sample"),
        #     ("LAT_NAD27",     "lat_nad27"),
        #     ("LONG_NAD27",    "long_nad27"),
        #     ("LAT_NAD83",     "lat_nad83"),
        #     ("LONG_NAD83",    "long_nad83"),
        #     ("X_NAD27",       "x_nad27"),
        #     ("Y_NAD27",       "y_nad27"),
        #     ("X_NAD83",       "x_nad83"),
        #     ("Y_NAD83",       "y_nad83"),
        #     ("ZONE",          "zone"),
        #     ("EARTHMAT_TYPE", "earthmat_type"),
        #     ("STATUS",        "status"),
        # ],
    )

    def get_by_name(self, name: str) -> int:
        # NOTE: This assumes that SAMPLE is unique on its own. If multiple rows have the same name, an error will be thrown.
        row_idxes = [row_idx for k, row_idx in self.indexes[('SURVEY_TITLE', 'STATION', 'EARTHMAT', 'SAMPLE')].items() if k[3] == name]
        assert len(row_idxes) <= 1
        return self.get_by_row_idx(row_idxes[0]) if len(row_idxes) else None


class BulkInterface(AnalysisDatasetWorkbook):
    _meta = utils.Meta(
        workbook_name = "BULK.xlsx"
    )
