import copy
import os

from openpyxl import load_workbook
import pandas as pd
import pytest

from geochem_dataset.excel import Dataset
from geochem_dataset.excel.exceptions import IntegrityError

from .conftest import ERROR_MESSAGES


class TestSurveysValid:
    def test_surveys(self, fixture_dataset_excel):
        dataset_path, dataset_excel_data = fixture_dataset_excel
        dataset_excel_data.to_excel(dataset_path)

        expected_surveys_worksheet_data = dataset_excel_data.workbooks['SURVEYS.xlsx'].worksheets['SURVEYS']
        expected_surveys = list(expected_surveys_worksheet_data.iter_objects())

        with Dataset(dataset_path) as dataset:
            surveys = list(dataset.surveys)
            assert surveys == expected_surveys

    def test_surveys_with_extra_columns_ok(self, fixture_dataset_excel):
        dataset_path, dataset_excel_data = fixture_dataset_excel
        dataset_excel_data.to_excel(dataset_path)

        surveys_path = dataset_path / 'SURVEYS.xlsx'
        df = pd.read_excel(surveys_path, sheet_name='SURVEYS')

        with pd.ExcelWriter(surveys_path) as writer:
            df['CAT'] = ['Skittles'] * len(df)
            df.to_excel(writer, sheet_name='SURVEYS', index=False)

        expected_dataset_excel_data = copy.deepcopy(dataset_excel_data)
        expected_survey_worksheet_data = expected_dataset_excel_data.workbooks['SURVEYS.xlsx'].worksheets['SURVEYS']
        expected_survey_worksheet_data.Meta.extra_headings = ('CAT',)
        for x in expected_survey_worksheet_data.data['surveys']:
            x += ['Skittles']
        expected_surveys = list(expected_survey_worksheet_data.iter_objects())

        with Dataset(dataset_path, extra_columns_ok=True) as dataset:
            surveys = list(dataset.surveys)
            assert surveys == expected_surveys


class TestSurveysInvalid:
    def test_surveys_with_empty_file(self, fixture_dataset_excel):
        dataset_path, dataset_excel_data = fixture_dataset_excel
        dataset_excel_data.to_excel(dataset_path)

        surveys_path = dataset_path / 'SURVEYS.xlsx'
        os.truncate(surveys_path, 0)

        with pytest.raises(ValueError) as excinfo:
            with Dataset(dataset_path) as dataset:
                pass

    def test_surveys_with_missing_sheet(self, fixture_dataset_excel):
        dataset_path, dataset_excel_data = fixture_dataset_excel
        dataset_excel_data.to_excel(dataset_path)

        surveys_path = dataset_path / 'SURVEYS.xlsx'

        wb = load_workbook(surveys_path)
        ws = wb['SURVEYS']
        ws.title = "Skittles"
        wb.save(surveys_path)

        expected_error_msg_kwargs = {
            'workbook' : 'SURVEYS.xlsx',
            'worksheet': 'SURVEYS',
        }

        with pytest.raises(IntegrityError) as excinfo:
            with Dataset(dataset_path) as dataset:
                pass

        assert excinfo.value.args[0] == ERROR_MESSAGES['missing_worksheet'].format(**expected_error_msg_kwargs)

    def test_surveys_with_missing_columns(self, fixture_dataset_excel):
        dataset_path, dataset_excel_data = fixture_dataset_excel
        dataset_excel_data.to_excel(dataset_path)

        surveys_path = dataset_path / 'SURVEYS.xlsx'

        with pd.ExcelWriter(surveys_path) as writer:
            df = pd.DataFrame()
            df.to_excel(writer, sheet_name='SURVEYS', index=False)

        expected_error_msg_kwargs = {
            'workbook' : 'SURVEYS.xlsx',
            'worksheet': 'SURVEYS',
            'columns'  : 'DESCRIPTION, GSC_CATALOG_NUMBER, ORGANIZATION, PARTY_LEADER, TITLE, YEAR_BEGIN, YEAR_END',
        }

        with pytest.raises(IntegrityError) as excinfo:
            with Dataset(dataset_path) as dataset:
                pass

        assert excinfo.value.args[0] == ERROR_MESSAGES['missing_columns'].format(**expected_error_msg_kwargs)

    def test_surveys_with_extra_columns_not_ok(self, fixture_dataset_excel):
        dataset_path, dataset_excel_data = fixture_dataset_excel
        dataset_excel_data.to_excel(dataset_path)

        surveys_path = dataset_path / 'SURVEYS.xlsx'
        df = pd.read_excel(surveys_path, sheet_name='SURVEYS')

        with pd.ExcelWriter(surveys_path) as writer:
            df['DOG'] = ['Yoru'] * len(df)
            df['CAT'] = ['Skittles'] * len(df)
            df.to_excel(writer, sheet_name='SURVEYS', index=False)

        expected_error_msg_kwargs = {
            'workbook' : 'SURVEYS.xlsx',
            'worksheet': 'SURVEYS',
            'columns'  : 'CAT, DOG',
        }

        with pytest.raises(IntegrityError) as excinfo:
            with Dataset(dataset_path) as dataset:
                pass

        assert excinfo.value.args[0] == ERROR_MESSAGES['extra_columns'].format(**expected_error_msg_kwargs)

    def test_surveys_with_no_data(self, fixture_dataset_excel):
        dataset_path, dataset_excel_data = fixture_dataset_excel
        dataset_excel_data.to_excel(dataset_path)

        surveys_path = dataset_path / 'SURVEYS.xlsx'
        df = pd.read_excel(surveys_path, sheet_name='SURVEYS')

        with pd.ExcelWriter(surveys_path) as writer:
            df = df[0:0]
            df.to_excel(writer, sheet_name='SURVEYS', index=False)

        expected_error_msg_kwargs = {
            'workbook': 'SURVEYS.xlsx',
            'worksheet': 'SURVEYS',
            'min_rows': 1,
            'max_rows': 'unlimited',
        }

        with pytest.raises(IntegrityError) as excinfo:
            with Dataset(dataset_path) as dataset:
                pass

        assert excinfo.value.args[0] == ERROR_MESSAGES['too_few_rows'].format(**expected_error_msg_kwargs)

    def test_surveys_with_too_much_data(self):
        assert True  # Not necessary since an unlimited number of rows is permitted

    def test_surveys_with_duplicate(self, fixture_dataset_excel):
        dataset_path, dataset_excel_data = fixture_dataset_excel
        dataset_excel_data.to_excel(dataset_path)

        surveys_path = dataset_path / 'SURVEYS.xlsx'
        df = pd.read_excel(surveys_path, sheet_name='SURVEYS')

        with pd.ExcelWriter(surveys_path) as writer:
            df = pd.concat([df, df], ignore_index=True)
            df.to_excel(writer, sheet_name='SURVEYS', index=False)

        expected_error_msg_kwargs = {
            'workbook' : 'SURVEYS.xlsx',
            'worksheet': 'SURVEYS',
            'row'      : 3,
            'columns'  : 'TITLE',
            'other_row': 2
        }

        with pytest.raises(IntegrityError) as excinfo:
            with Dataset(dataset_path) as dataset:
                pass

        assert excinfo.value.args[0] == ERROR_MESSAGES['unique_constraint_violation'].format(**expected_error_msg_kwargs)
