import copy
import os

from openpyxl import load_workbook
import pandas as pd
import pytest

from geochem_dataset.excel import Dataset
from geochem_dataset.excel.exceptions import IntegrityError

from .conftest import ERROR_MESSAGES
from ..helpers.utils import xlrowref


class TestSamplesValid:
    def test_samples(self, fixture_dataset_excel):
        dataset_path, dataset_excel_data = fixture_dataset_excel
        dataset_excel_data.to_excel(dataset_path)

        expected_samples_worksheet_data = dataset_excel_data.workbooks['SAMPLES.xlsx'].worksheets['SAMPLES']
        expected_samples = list(expected_samples_worksheet_data.iter_objects())

        with Dataset(dataset_path) as dataset:
            samples = list(dataset.samples)
            assert samples == expected_samples

    def test_samples_with_extra_columns_ok(self, fixture_dataset_excel):
        dataset_path, dataset_excel_data = fixture_dataset_excel
        dataset_excel_data.to_excel(dataset_path)

        samples_path = dataset_path / 'SAMPLES.xlsx'
        df = pd.read_excel(samples_path, sheet_name='SAMPLES')

        with pd.ExcelWriter(samples_path) as writer:
            df['CAT'] = ['Skittles'] * len(df)
            df.to_excel(writer, sheet_name='SAMPLES', index=False)

        expected_dataset_excel_data = copy.deepcopy(dataset_excel_data)
        expected_sample_worksheet_data = expected_dataset_excel_data.workbooks['SAMPLES.xlsx'].worksheets['SAMPLES']
        expected_sample_worksheet_data.Meta.extra_headings = ('CAT',)
        for x in expected_sample_worksheet_data.data['samples']:
            x += ['Skittles']
        expected_samples = list(expected_sample_worksheet_data.iter_objects())

        with Dataset(dataset_path, extra_columns_ok=True) as dataset:
            samples = list(dataset.samples)
            assert samples == expected_samples


class TestSamplesInvalid:
    def test_samples_with_empty_file(self, fixture_dataset_excel):
        dataset_path, dataset_excel_data = fixture_dataset_excel
        dataset_excel_data.to_excel(dataset_path)

        samples_path = dataset_path / 'SAMPLES.xlsx'
        os.truncate(samples_path, 0)

        with pytest.raises(ValueError) as excinfo:
            with Dataset(dataset_path) as dataset:
                pass

    def test_samples_with_missing_sheet(self, fixture_dataset_excel):
        dataset_path, dataset_excel_data = fixture_dataset_excel
        dataset_excel_data.to_excel(dataset_path)

        samples_path = dataset_path / 'SAMPLES.xlsx'
        wb = load_workbook(samples_path)
        ws = wb['SAMPLES']
        ws.title = "Skittles"
        wb.save(samples_path)

        expected_error_msg_kwargs = {
            'workbook' : 'SAMPLES.xlsx',
            'worksheet': 'SAMPLES',
        }

        with pytest.raises(IntegrityError) as excinfo:
            with Dataset(dataset_path) as dataset:
                pass

        assert excinfo.value.args[0] == ERROR_MESSAGES['missing_worksheet'].format(**expected_error_msg_kwargs)

    def test_samples_with_missing_columns(self, fixture_dataset_excel):
        dataset_path, dataset_excel_data = fixture_dataset_excel
        dataset_excel_data.to_excel(dataset_path)

        samples_path = dataset_path / 'SAMPLES.xlsx'

        with pd.ExcelWriter(samples_path) as writer:
            df = pd.DataFrame()
            df.to_excel(writer, sheet_name='SAMPLES', index=False)

        expected_error_msg_kwargs = {
            'workbook' : 'SAMPLES.xlsx',
            'worksheet': 'SAMPLES',
            'columns'  : "EARTHMAT, EARTHMAT_TYPE, LAT_NAD27, LAT_NAD83, LONG_NAD27, LONG_NAD83, SAMPLE, STATION, STATUS, SURVEY_TITLE, X_NAD27, X_NAD83, Y_NAD27, Y_NAD83, ZONE"
        }

        with pytest.raises(IntegrityError) as excinfo:
            with Dataset(dataset_path) as dataset:
                pass

        assert excinfo.value.args[0] == ERROR_MESSAGES['missing_columns'].format(**expected_error_msg_kwargs)

    def test_samples_with_extra_columns_not_ok(self, fixture_dataset_excel):
        dataset_path, dataset_excel_data = fixture_dataset_excel
        dataset_excel_data.to_excel(dataset_path)

        samples_path = dataset_path / 'SAMPLES.xlsx'
        df = pd.read_excel(samples_path, sheet_name='SAMPLES')

        with pd.ExcelWriter(samples_path) as writer:
            df['DOG'] = ['Yoru'] * len(df)
            df['CAT'] = ['Skittles'] * len(df)
            df.to_excel(writer, sheet_name='SAMPLES', index=False)

        expected_error_msg_kwargs = {
            'workbook' : 'SAMPLES.xlsx',
            'worksheet': 'SAMPLES',
            'columns'  : 'CAT, DOG',
        }

        with pytest.raises(IntegrityError) as excinfo:
            with Dataset(dataset_path) as datasetError:
                pass

        assert excinfo.value.args[0] == ERROR_MESSAGES['extra_columns'].format(**expected_error_msg_kwargs)

    def test_samples_with_no_data(self, fixture_dataset_excel):
        dataset_path, dataset_excel_data = fixture_dataset_excel
        dataset_excel_data.to_excel(dataset_path)

        samples_path = dataset_path / 'SAMPLES.xlsx'
        df = pd.read_excel(samples_path, sheet_name='SAMPLES')

        with pd.ExcelWriter(samples_path) as writer:
            df = df[0:0]
            df.to_excel(writer, sheet_name='SAMPLES', index=False)

        expected_error_msg_kwargs = {
            'workbook' : 'SAMPLES.xlsx',
            'worksheet': 'SAMPLES',
            'min_rows' : 1,
            'max_rows' : 'unlimited',
        }

        with pytest.raises(IntegrityError) as excinfo:
            with Dataset(dataset_path) as _:
                pass

        assert excinfo.value.args[0] == ERROR_MESSAGES['too_few_rows'].format(**expected_error_msg_kwargs)

    def test_samples_with_too_much_data(self):
        assert True  # Not necessary since only an unlimited number of rows are allowed

    def test_samples_with_duplicate(self, fixture_dataset_excel):
        dataset_path, dataset_excel_data = fixture_dataset_excel
        dataset_excel_data.to_excel(dataset_path)

        samples_path = dataset_path / 'SAMPLES.xlsx'
        df = pd.read_excel(samples_path, sheet_name='SAMPLES')

        with pd.ExcelWriter(samples_path) as writer:
            df = pd.concat([df, df], ignore_index=True)
            df.to_excel(writer, sheet_name='SAMPLES', index=False)

        expected_error_msg_kwargs = {
            'workbook' : 'SAMPLES.xlsx',
            'worksheet': 'SAMPLES',
            'row'      : 6,
            'columns'  : 'SURVEY_TITLE, STATION, EARTHMAT, SAMPLE',
            'other_row': 2
        }

        with pytest.raises(IntegrityError) as excinfo:
            with Dataset(dataset_path) as dataset:
                pass

        assert excinfo.value.args[0] == ERROR_MESSAGES['unique_constraint_violation'].format(**expected_error_msg_kwargs)

    def test_samples_with_non_existant_survey_title(self, fixture_dataset_excel):
        dataset_path, dataset_excel_data = fixture_dataset_excel
        dataset_excel_data.to_excel(dataset_path)

        samples_path = dataset_path / 'SAMPLES.xlsx'
        df = pd.read_excel(samples_path, sheet_name='SAMPLES')

        with pd.ExcelWriter(samples_path) as writer:
            df['SURVEY_TITLE'] = df.iloc[0]['SURVEY_TITLE'] + '-different'
            df.to_excel(writer, sheet_name='SAMPLES', index=False)

        expected_error_msg_kwargs = {
            'workbook'    : 'SAMPLES.xlsx',
            'worksheet'   : 'SAMPLES',
            'row'         : xlrowref(1),
            'column'      : 'SURVEY_TITLE',
            'fk_workbook' : 'SURVEYS.xlsx',
            'fk_worksheet': 'SURVEYS',
            'fk_column'   : 'TITLE',
        }

        # Assert

        with pytest.raises(IntegrityError) as excinfo:
            with Dataset(dataset_path) as dataset:
                pass

        assert excinfo.value.args[0] == ERROR_MESSAGES['foreign_key_constraint_violation'].format(**expected_error_msg_kwargs)

    def test_samples_with_non_float_lat_long(self, fixture_dataset_excel):
        dataset_path, dataset_excel_data = fixture_dataset_excel
        dataset_excel_data.to_excel(dataset_path)

        samples_path = dataset_path / 'SAMPLES.xlsx'
        df = pd.read_excel(samples_path, sheet_name='SAMPLES')

        with pd.ExcelWriter(samples_path) as writer:
            df.iloc[0, 4] = 'ABC'
            df.to_excel(writer, sheet_name='SAMPLES', index=False)

        expected_error_msg_kwargs = {
            'workbook' : 'SAMPLES.xlsx',
            'worksheet': 'SAMPLES',
            'row'      : xlrowref(1),
            'column'   : 'LAT_NAD27',
        }

        with pytest.raises(IntegrityError) as excinfo:
            with Dataset(dataset_path) as dataset:
                pass

        assert excinfo.value.args[0] == ERROR_MESSAGES['invalid_value'].format(**expected_error_msg_kwargs)
