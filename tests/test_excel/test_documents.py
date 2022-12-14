import copy
import os
from pathlib import Path

from openpyxl import load_workbook
import pandas as pd
import pytest
import yaml

from geochem_dataset.excel import Dataset
from geochem_dataset.excel.exceptions import IntegrityError

from .conftest import ERROR_MESSAGES


class TestDocumentsValid:
    def test_documents(self, fixture_dataset_excel):
        dataset_path, dataset_excel_data = fixture_dataset_excel
        dataset_excel_data.to_excel(dataset_path)

        expected_document_worksheet_data = dataset_excel_data.workbooks['DOCUMENT.xlsx'].worksheets['DOCUMENT']
        expected_documents = list(expected_document_worksheet_data.iter_objects())

        with Dataset(dataset_path) as dataset:
            documents = list(dataset.documents)
            assert documents == expected_documents

    def test_documents_with_extra_columns_ok(self, fixture_dataset_excel):
        dataset_path, dataset_excel_data = fixture_dataset_excel
        dataset_excel_data.to_excel(dataset_path)

        document_path = dataset_path / 'DOCUMENT.xlsx'
        df = pd.read_excel(document_path, sheet_name='DOCUMENT')

        with pd.ExcelWriter(document_path) as writer:
            df['CAT'] = ['Skittles']
            df.to_excel(writer, sheet_name='DOCUMENT', index=False)

        expected_dataset_excel_data = copy.deepcopy(dataset_excel_data)
        expected_document_worksheet_data = expected_dataset_excel_data.workbooks['DOCUMENT.xlsx'].worksheets['DOCUMENT']
        expected_document_worksheet_data.Meta.extra_headings = ('CAT',)
        expected_document_worksheet_data.data['documents'][0] += ['Skittles']
        expected_documents = list(expected_document_worksheet_data.iter_objects())

        with Dataset(dataset_path, extra_columns_ok=True) as dataset:
            documents = list(dataset.documents)
            assert documents == expected_documents


class TestDocumentsInvalid:
    def test_documents_with_empty_file(self, fixture_dataset_excel):
        dataset_path, dataset_excel_data = fixture_dataset_excel
        dataset_excel_data.to_excel(dataset_path)

        document_path = dataset_path / 'DOCUMENT.xlsx'
        os.truncate(document_path, 0)

        with pytest.raises(ValueError) as excinfo:
            with Dataset(dataset_path) as dataset:
                pass

    def test_documents_with_missing_sheet(self, fixture_dataset_excel):
        dataset_path, dataset_excel_data = fixture_dataset_excel
        dataset_excel_data.to_excel(dataset_path)

        document_path = dataset_path / 'DOCUMENT.xlsx'
        wb = load_workbook(document_path)
        ws = wb['DOCUMENT']
        ws.title = "Skittles"
        wb.save(document_path)

        expected_error_msg_kwargs = {
            'workbook': 'DOCUMENT.xlsx',
            'worksheet': 'DOCUMENT',
        }

        with pytest.raises(IntegrityError) as excinfo:
            with Dataset(dataset_path) as dataset:
                pass

        assert excinfo.value.args[0] == ERROR_MESSAGES['missing_worksheet'].format(**expected_error_msg_kwargs)

    def test_documents_with_missing_columns(self, fixture_dataset_excel):
        dataset_path, dataset_excel_data = fixture_dataset_excel
        dataset_excel_data.to_excel(dataset_path)

        document_path = dataset_path / 'DOCUMENT.xlsx'

        with pd.ExcelWriter(document_path) as writer:
            df = pd.DataFrame()
            df.to_excel(writer, sheet_name='DOCUMENT', index=False)

        expected_error_msg_kwargs = {
            'workbook': 'DOCUMENT.xlsx',
            'worksheet': 'DOCUMENT',
            'columns': "RECOMMENDED_CITATION"
        }

        with pytest.raises(IntegrityError) as excinfo:
            with Dataset(dataset_path) as dataset:
                pass

        assert excinfo.value.args[0] == ERROR_MESSAGES['missing_columns'].format(**expected_error_msg_kwargs)

    def test_documents_with_extra_columns_not_ok(self, fixture_dataset_excel):
        dataset_path, dataset_excel_data = fixture_dataset_excel
        dataset_excel_data.to_excel(dataset_path)

        document_path = dataset_path / 'DOCUMENT.xlsx'

        df = pd.read_excel(document_path, sheet_name='DOCUMENT')

        with pd.ExcelWriter(document_path) as writer:
            df['DOG'] = ['Yoru']
            df['CAT'] = ['Skittles']
            df.to_excel(writer, sheet_name='DOCUMENT', index=False)

        expected_error_msg_kwargs = {
            'workbook': 'DOCUMENT.xlsx',
            'worksheet': 'DOCUMENT',
            'columns': 'CAT, DOG',
        }

        with pytest.raises(IntegrityError) as excinfo:
            with Dataset(dataset_path) as datasetError:
                pass

        assert excinfo.value.args[0] == ERROR_MESSAGES['extra_columns'].format(**expected_error_msg_kwargs)

    def test_documents_with_no_data(self, fixture_dataset_excel):
        dataset_path, dataset_excel_data = fixture_dataset_excel
        dataset_excel_data.to_excel(dataset_path)

        document_path = dataset_path / 'DOCUMENT.xlsx'
        df = pd.read_excel(document_path, sheet_name='DOCUMENT')

        with pd.ExcelWriter(document_path) as writer:
            df = df[0:0]
            df.to_excel(writer, sheet_name='DOCUMENT', index=False)

        expected_error_msg_kwargs = {
            'workbook': 'DOCUMENT.xlsx',
            'worksheet': 'DOCUMENT',
            'min_rows': 1,
            'max_rows': 1,
        }

        with pytest.raises(IntegrityError) as excinfo:
            with Dataset(dataset_path) as dataset:
                pass

        assert excinfo.value.args[0] == ERROR_MESSAGES['too_few_rows'].format(**expected_error_msg_kwargs)

    def test_documents_with_too_much_data(self, fixture_dataset_excel):
        dataset_path, dataset_excel_data = fixture_dataset_excel
        dataset_excel_data.to_excel(dataset_path)

        document_path = dataset_path / 'DOCUMENT.xlsx'
        df = pd.read_excel(document_path, sheet_name='DOCUMENT')

        with pd.ExcelWriter(document_path) as writer:
            df = pd.concat([df, df.iloc[0].to_frame().T], ignore_index=True)
            df.to_excel(writer, sheet_name='DOCUMENT', index=False)

        expected_error_msg_kwargs = {
            'workbook': 'DOCUMENT.xlsx',
            'worksheet': 'DOCUMENT',
            'min_rows': 1,
            'max_rows': 1,
        }

        with pytest.raises(IntegrityError) as excinfo:
            with Dataset(dataset_path) as dataset:
                pass

        assert excinfo.value.args[0] == ERROR_MESSAGES['too_many_rows'].format(**expected_error_msg_kwargs)

    def test_documents_with_duplicate(self):
        assert True  # Not necessary since only one row is permitted
