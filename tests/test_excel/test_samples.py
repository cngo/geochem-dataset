import os

import numpy as np
from openpyxl import load_workbook
import pandas as pd
import pytest

from geochem_dataset.excel import Dataset
from geochem_dataset.excel.dataclasses import Sample, Survey
from geochem_dataset.excel.exceptions import IntegrityError

from tests.test_excel.helpers.utils import xlref, xlrowref, xlcolref

SURVEYS = [
    Survey('2011, Till sampling survey, Hall Peninsula. Canada-Nunavut Geoscience Office', 'Canada-Nunavut Geoscience Office', 2011, 2013, 'Tremblay, Tommy', 'A test description', 1000),
]

TEST_FILE_NAME = 'SAMPLES.xlsx'
TEST_SHEET_NAME = 'SAMPLES'
TEST_COLUMNS = ('SURVEY_TITLE', 'STATION', 'EARTHMAT', 'SAMPLE', 'LAT_NAD27', 'LONG_NAD27', 'LAT_NAD83', 'LONG_NAD83', 'X_NAD27', 'Y_NAD27', 'X_NAD83', 'Y_NAD83', 'ZONE', 'EARTHMAT_TYPE', 'STATUS')
TEST_DATA = [
    ('2011, Till sampling survey, Hall Peninsula. Canada-Nunavut Geoscience Office', '11TIAT001', '11TIAT001A', '11TIAT001A01', None, None, 64.010103, -67.351092, None, None, None, None, None, 'Till', None),
    ('2011, Till sampling survey, Hall Peninsula. Canada-Nunavut Geoscience Office', '11TIAT024', '11TIAT024A', '11TIAT024A01', None, None, 64.472825, -67.721319, None, None, None, None, None, 'Till', None),
    ('2011, Till sampling survey, Hall Peninsula. Canada-Nunavut Geoscience Office', '12TIAT138', '12TIAT138A', '12TIAT138A01', None, None, 64.209300, -67.011316, None, None, None, None, None, 'Till', None),
    ('2011, Till sampling survey, Hall Peninsula. Canada-Nunavut Geoscience Office', '12TIAT139', '12TIAT139A', '12TIAT139A01', None, None, 64.334217, -67.087329, None, None, None, None, None, 'Till', None),
]

ERROR_MESSAGES = {
    'missing_worksheet':                'Worksheet {worksheet} is missing from workbook {workbook}',
    'missing_columns':                  'Worksheet {workbook}::{worksheet} is missing columns: {column_names}',
    'extra_columns':                    'Worksheet {workbook}::{worksheet} has extra columns: {column_names}',
    'too_few_rows':                     'Worksheet {workbook}::{worksheet} has too few rows (min is {min_rows} and max is {max_rows})',
    'unique_constraint_violation':      'Row {row} of worksheet {workbook}::{worksheet} violated a unique constraint on columns: {columns} (duplicate of row {other_row})',
    'foreign_key_constraint_violation': 'Row {row} of worksheet {workbook}::{worksheet} violated a foreign constraint on column {column} (references column {fk_column} in worksheet {fk_workbook}::{fk_worksheet})',
    'invalid_value':                    'Row {row} in worksheet {workbook}::{worksheet} has an invalid value for column {column}'
}


def get_survey_by_title(title):
    for survey in SURVEYS:
        if survey.title == title:
            return survey


class TestSamples:
    def test_samples(self, dataset_path):
        # Build expected

        expected_samples = []

        for args in TEST_DATA:
            args = list(args)
            args[0] = get_survey_by_title(args[0])
            expected_samples.append(Sample(*args))

        # Assert

        with Dataset(dataset_path) as dataset:
            samples = list(dataset.samples)
            assert samples == expected_samples

    def test_samples_with_empty_file(self, dataset_path):
        # Modify samples file

        samples_path = dataset_path / TEST_FILE_NAME
        os.truncate(samples_path, 0)

        # Assert

        with pytest.raises(ValueError) as excinfo:
            with Dataset(dataset_path) as dataset:
                pass

    def test_samples_with_missing_sheet(self, dataset_path):
        # Modify samples file

        samples_path = dataset_path / TEST_FILE_NAME

        wb = load_workbook(samples_path)
        ws = wb[TEST_SHEET_NAME]
        ws.title = "Skittles"
        wb.save(samples_path)

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


    def test_samples_with_missing_columns(self, dataset_path):
        # Modify samples file

        samples_path = dataset_path / TEST_FILE_NAME

        with pd.ExcelWriter(samples_path) as writer:
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

    def test_samples_with_extra_columns(self, dataset_path):
        # Modify samples file

        samples_path = dataset_path / TEST_FILE_NAME

        df = pd.read_excel(samples_path, sheet_name=TEST_SHEET_NAME)

        with pd.ExcelWriter(samples_path) as writer:
            df['DOG'] = 'Yoru'
            df['CAT'] = 'Skittles'
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

    def test_samples_with_extra_columns_ok(self, dataset_path):
        # Modify file

        samples_path = dataset_path / TEST_FILE_NAME

        df = pd.read_excel(samples_path, sheet_name=TEST_SHEET_NAME)

        with pd.ExcelWriter(samples_path) as writer:
            df['CAT'] = ['Skittles', 'Duchess', 'Yoru', 'Bobbie']
            df.to_excel(writer, sheet_name=TEST_SHEET_NAME, index=False)

        # Build expected

        NEW_TEST_DATA = TEST_DATA.copy()
        NEW_TEST_DATA[0] += (frozenset((('cat', 'Skittles'),)),)
        NEW_TEST_DATA[1] += (frozenset((('cat', 'Duchess'),)),)
        NEW_TEST_DATA[2] += (frozenset((('cat', 'Yoru'),)),)
        NEW_TEST_DATA[3] += (frozenset((('cat', 'Bobbie'),)),)

        expected_samples = []

        for args in NEW_TEST_DATA:
            args = list(args)
            args[0] = get_survey_by_title(args[0])
            expected_samples.append(Sample(*args))

        # Assert

        with Dataset(dataset_path, extra_columns_ok=True) as dataset:
            samples = list(dataset.samples)
            assert samples == expected_samples

    def test_samples_with_no_data(self, dataset_path):
        # Modify samples file

        samples_path = dataset_path / TEST_FILE_NAME

        df = pd.read_excel(samples_path, sheet_name=TEST_SHEET_NAME)

        with pd.ExcelWriter(samples_path) as writer:
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

    def test_samples_with_too_much_data(self, dataset_path):
        assert True  # Not necessary since an unlimited number of rows is permitted

    def test_samples_with_non_existant_survey_title(self, dataset_path):
        # Modify samples file

        samples_path = dataset_path / TEST_FILE_NAME

        df = pd.read_excel(samples_path, sheet_name=TEST_SHEET_NAME)

        with pd.ExcelWriter(samples_path) as writer:
            df['SURVEY_TITLE'] = df.iloc[0]['SURVEY_TITLE'] + '-different'
            df.to_excel(writer, sheet_name=TEST_SHEET_NAME, index=False)

        # Expected

        expected_error_msg_kwargs = {
            'workbook': TEST_FILE_NAME,
            'worksheet': TEST_SHEET_NAME,
            'row': xlrowref(1),
            'column': 'SURVEY_TITLE',
            'fk_workbook': 'SURVEYS.xlsx',
            'fk_worksheet': 'SURVEYS',
            'fk_column': 'TITLE',
        }

        # Assert

        with pytest.raises(IntegrityError) as excinfo:
            with Dataset(dataset_path) as dataset:
                pass

        assert excinfo.value.args[0] == ERROR_MESSAGES['foreign_key_constraint_violation'].format(**expected_error_msg_kwargs)

    def test_samples_with_duplicate(self, dataset_path):
        # Modify samples file

        samples_path = dataset_path / TEST_FILE_NAME

        df = pd.read_excel(samples_path, sheet_name=TEST_SHEET_NAME)

        with pd.ExcelWriter(samples_path) as writer:
            df = df.append(df.copy(), ignore_index=True)
            df.to_excel(writer, sheet_name=TEST_SHEET_NAME, index=False)

        # Expected

        expected_error_msg_kwargs = {
            'workbook': TEST_FILE_NAME,
            'worksheet': TEST_SHEET_NAME,
            'row': 6,
            'columns': 'SURVEY_TITLE, STATION, EARTHMAT, SAMPLE',
            'other_row': 2
        }

        # Assert

        with pytest.raises(IntegrityError) as excinfo:
            with Dataset(dataset_path) as dataset:
                pass

        assert excinfo.value.args[0] == ERROR_MESSAGES['unique_constraint_violation'].format(**expected_error_msg_kwargs)

    def test_samples_with_non_float_lat_long(self, dataset_path):
        # Modify

        surveys_path = dataset_path / TEST_FILE_NAME

        df = pd.read_excel(surveys_path, sheet_name=TEST_SHEET_NAME)

        with pd.ExcelWriter(surveys_path) as writer:
            df.iloc[0, 4] = 'ABC'
            df.to_excel(writer, sheet_name=TEST_SHEET_NAME, index=False)

        # Expected

        expected_error_msg_kwargs = {
            'workbook': TEST_FILE_NAME,
            'worksheet': TEST_SHEET_NAME,
            'row': xlrowref(1),
            'column': 'LAT_NAD27',
        }

        # Assert

        with pytest.raises(IntegrityError) as excinfo:
            with Dataset(dataset_path) as dataset:
                pass

        assert excinfo.value.args[0] == ERROR_MESSAGES['invalid_value'].format(**expected_error_msg_kwargs)
