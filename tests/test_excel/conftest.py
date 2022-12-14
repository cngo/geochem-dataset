from pathlib import Path

import pytest
import yaml

from .helpers.dataset_excel_data import DatasetExcelData


FIXTURE_DATASET_NAME = 'ca.cngo.test'
FIXTURE_DATASET_EXCEL_DATA_PATH = Path(__file__).parent / 'fixture_dataset_excel_data.yaml'

ERROR_MESSAGES = {
    'missing_worksheet'               : 'Worksheet {worksheet} is missing from workbook {workbook}',
    'missing_columns'                 : 'Worksheet {workbook}::{worksheet} is missing columns: {columns}',
    'extra_columns'                   : 'Worksheet {workbook}::{worksheet} has extra columns: {columns}',
    'too_few_rows'                    : 'Worksheet {workbook}::{worksheet} has too few rows (min is {min_rows} and max is {max_rows})',
    'too_many_rows'                   : 'Worksheet {workbook}::{worksheet} has too many rows (min is {min_rows} and max is {max_rows})',
    'unique_constraint_violation'     : 'Row {row} of worksheet {workbook}::{worksheet} violated a unique constraint on columns: {columns} (duplicate of row {other_row})',
    'foreign_key_constraint_violation': 'Row {row} of worksheet {workbook}::{worksheet} violated a foreign constraint on column {column} (references column {fk_column} in worksheet {fk_workbook}::{fk_worksheet})',
    'invalid_value'                   : 'Row {row} in worksheet {workbook}::{worksheet} has an invalid value for column {column}',

    # new form

    'empty_value__column'                 : 'Empty value for column {column} of row {row}',
    'empty_value__row'                    : 'Empty value for row {row} of column {column}',
    'fk_constraint_violation__columns'    : 'Value(s) for column(s) {columns} of row {row} does not exist in {fk_workbook}',
    'unique_constraint_violation__columns': 'Value(s) for column(s) {columns} of row {row} is a duplicate of row {duplicate_of_row}',



    'cell_not_empty': 'Cell {cell} is expected to be empty; {reason}',


    'result_type__missing': 'Result type is missing for cell {cell}'
}

ANALYSIS_WORKBOOK_ERROR_MESSAGES = {
    'sample_heading_missing':                  'Cell must be "SAMPLE"',
    'subsample_heading_missing':               'Cell must be "SUBSAMPLE"',
    'metadata_type_heading_missing':           'Cell must be "METADATA_TYPE"',
    'region_left_of_metadata_types_not_empty': 'Region left of metadata types is not empty',
    'metadata_type_missing':                   'Metadata type is missing in cell {cell} of worksheet {workbook}::{worksheet}',
    'metadata_type_duplicate':                 'Metadata type in cell {cell} of worksheet {workbook}::{worksheet} is a duplicate',
    'result_type_metadata_pair_duplicate':     'Result type-metadata pair in column {column} of worksheet {workbook}::{worksheet} is a duplicate',
    'subsample_values_missing':                'Missing value(s) for subsample in row {row} of worksheet {workbook}::{worksheet}',
    'sample_does_not_exist':                   'Sample in cell {cell} of worksheet {workbook}::{worksheet} does not exist',
    'subsample_duplicate':                     'Subsample in row {row} of worksheet {workbook}::{worksheet} is a duplicate',
    'missing_result_type':                     'Missing result type'
}



@pytest.fixture
def fixture_dataset_excel(tmp_path) -> tuple[Path, DatasetExcelData]:
    dataset_path = tmp_path / FIXTURE_DATASET_NAME
    dataset_path.mkdir()

    with FIXTURE_DATASET_EXCEL_DATA_PATH.open() as f:
        fixture_data = yaml.load(f, Loader=yaml.SafeLoader)

    dataset_excel_data = DatasetExcelData.from_dict(fixture_data)

    return dataset_path, dataset_excel_data
