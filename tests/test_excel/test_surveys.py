import os

import numpy as np
from openpyxl import load_workbook
import pandas as pd
import pytest

from geochem_dataset.excel import Dataset
from geochem_dataset.excel.dataclasses import Survey
from geochem_dataset.excel.exceptions import IntegrityError

from helpers.utils import xlref, xlrowref, xlcolref

TEST_FILE_NAME = 'SURVEYS.xlsx'
TEST_SHEET_NAME = 'SURVEYS'
TEST_COLUMNS = ('TITLE', 'ORGANIZATION', 'YEAR_BEGIN', 'YEAR_END', 'PARTY_LEADER', 'DESCRIPTION', 'GSC_CATALOG_NUMBER')
TEST_DATA = [
    ('2011, Till sampling survey, Hall Peninsula. Canada-Nunavut Geoscience Office', 'Canada-Nunavut Geoscience Office', 2011, 2013, 'Tremblay, Tommy', 'A test description', 1000),
]

ERROR_MESSAGES = {
    'missing_worksheet':           'Worksheet {worksheet} is missing from workbook {workbook}',
    'missing_columns':             'Worksheet {workbook}::{worksheet} is missing columns: {column_names}',
    'extra_columns':               'Worksheet {workbook}::{worksheet} has extra columns: {column_names}',
    'too_few_rows':                'Worksheet {workbook}::{worksheet} has too few rows (min is {min_rows} and max is {max_rows})',
    'unique_constraint_violation': 'Row {row} of worksheet {workbook}::{worksheet} violated a unique constraint on columns: {columns} (duplicate of row {other_row})',
}


class TestSurveys:
    def test_surveys(self, dataset_path):
        # Build expected rows

        expected_surveys = [Survey(*args) for args in TEST_DATA]

        # Assert

        with Dataset(dataset_path) as dataset:
            surveys = list(dataset.surveys)
            assert surveys == expected_surveys

    def test_surveys_with_empty_file(self, dataset_path):
        # Modify surveys file

        surveys_path = dataset_path / TEST_FILE_NAME
        os.truncate(surveys_path, 0)

        # Assert

        with pytest.raises(ValueError) as excinfo:
            with Dataset(dataset_path) as dataset:
                pass

    def test_surveys_with_missing_sheet(self, dataset_path):
        # Modify surveys file

        surveys_path = dataset_path / TEST_FILE_NAME

        wb = load_workbook(surveys_path)
        ws = wb[TEST_SHEET_NAME]
        ws.title = "Skittles"
        wb.save(surveys_path)

        # Expected

        expected_error_msg_kwargs = {
            'workbook': TEST_FILE_NAME,
            'worksheet': TEST_SHEET_NAME,
        }

        # Assert

        with pytest.raises(IntegrityError) as excinfo:
            with Dataset(dataset_path) as dataset:
                pass

        assert excinfo.value.args[0] == ERROR_MESSAGES['missing_worksheet'].format(**expected_error_msg_kwargs)

    def test_surveys_with_missing_columns(self, dataset_path):
        # Modify surveys file

        surveys_path = dataset_path / TEST_FILE_NAME

        with pd.ExcelWriter(surveys_path) as writer:
            df = pd.DataFrame()
            df.to_excel(writer, sheet_name=TEST_SHEET_NAME, index=False)

        # Expected

        expected_error_msg_kwargs = {
            'workbook': TEST_FILE_NAME,
            'worksheet': TEST_SHEET_NAME,
            'column_names': ', '.join(sorted(TEST_COLUMNS)),
        }

        # Assert

        with pytest.raises(IntegrityError) as excinfo:
            with Dataset(dataset_path) as dataset:
                pass

        assert excinfo.value.args[0] == ERROR_MESSAGES['missing_columns'].format(**expected_error_msg_kwargs)

    def test_surveys_with_extra_columns(self, dataset_path):
        # Modify surveys file

        surveys_path = dataset_path / TEST_FILE_NAME

        df = pd.read_excel(surveys_path, sheet_name=TEST_SHEET_NAME)

        with pd.ExcelWriter(surveys_path) as writer:
            df['DOG'] = ['Yoru']
            df['CAT'] = ['Skittles']
            df.to_excel(writer, sheet_name=TEST_SHEET_NAME, index=False)

        # Expected

        expected_error_msg_kwargs = {
            'workbook': TEST_FILE_NAME,
            'worksheet': TEST_SHEET_NAME,
            'column_names': 'CAT, DOG',
        }

        # Assert

        with pytest.raises(IntegrityError) as excinfo:
            with Dataset(dataset_path) as datasetError:
                pass

        assert excinfo.value.args[0] == ERROR_MESSAGES['extra_columns'].format(**expected_error_msg_kwargs)

    def test_surveys_with_extra_columns_ok(self, dataset_path):
        # Modify surveys file

        surveys_path = dataset_path / TEST_FILE_NAME

        df = pd.read_excel(surveys_path, sheet_name=TEST_SHEET_NAME)

        with pd.ExcelWriter(surveys_path) as writer:
            df['CAT'] = ['Skittles']
            df.to_excel(writer, sheet_name=TEST_SHEET_NAME, index=False)

        # Build expected

        NEW_TEST_DATA = TEST_DATA.copy()
        NEW_TEST_DATA[0] = NEW_TEST_DATA[0] + (frozenset((('cat', 'Skittles'),)),)

        expected_surveys = [Survey(*args) for args in NEW_TEST_DATA]

        # Assert

        with Dataset(dataset_path, extra_columns_ok=True) as dataset:
            surveys = list(dataset.surveys)
            assert surveys == expected_surveys

    def test_surveys_with_no_data(self, dataset_path):
        # Modify surveys file

        surveys_path = dataset_path / TEST_FILE_NAME

        df = pd.read_excel(surveys_path, sheet_name=TEST_SHEET_NAME)

        with pd.ExcelWriter(surveys_path) as writer:
            df = df[0:0]
            df.to_excel(writer, sheet_name=TEST_SHEET_NAME, index=False)

        # Expected

        expected_error_msg_kwargs = {
            'workbook': TEST_FILE_NAME,
            'worksheet': TEST_SHEET_NAME,
            'min_rows': 1,
            'max_rows': 'unlimited',
        }

        # Assert

        with pytest.raises(IntegrityError) as excinfo:
            with Dataset(dataset_path) as dataset:
                pass

        assert excinfo.value.args[0] == ERROR_MESSAGES['too_few_rows'].format(**expected_error_msg_kwargs)

    def test_surveys_with_too_much_data(self, dataset_path):
        assert True  # Not necessary since an unlimited number of rows is permitted

    def test_surveys_with_duplicate_title(self, dataset_path):
        # Modify

        surveys_path = dataset_path / TEST_FILE_NAME

        df = pd.read_excel(surveys_path, sheet_name=TEST_SHEET_NAME)

        with pd.ExcelWriter(surveys_path) as writer:
            df = df.append(df.copy(), ignore_index=True)
            df.to_excel(writer, sheet_name=TEST_SHEET_NAME, index=False)

        # Expected

        expected_error_msg_kwargs = {
            'workbook': TEST_FILE_NAME,
            'worksheet': TEST_SHEET_NAME,
            'row': 3,
            'columns': 'TITLE',
            'other_row': 2
        }

        # Assert

        with pytest.raises(IntegrityError) as excinfo:
            with Dataset(dataset_path) as dataset:
                pass

        assert excinfo.value.args[0] == ERROR_MESSAGES['unique_constraint_violation'].format(**expected_error_msg_kwargs)
