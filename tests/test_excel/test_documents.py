import os

import numpy as np
from openpyxl import load_workbook
import pandas as pd
import pytest

from geochem_dataset.excel import Dataset
from geochem_dataset.excel.dataclasses import Document
from geochem_dataset.excel.exceptions import IntegrityError

from helpers.utils import xlref, xlrowref, xlcolref

TEST_FILE_NAME = 'DOCUMENT.xlsx'
TEST_SHEET_NAME = 'DOCUMENT'
TEST_COLUMNS = ('RECOMMENDED_CITATION',)
TEST_DATA = [
    ('A test citation',)
]

ERROR_MESSAGES = {
    'missing_worksheet': 'Worksheet {worksheet} is missing from workbook {workbook}',
    'missing_columns':   'Worksheet {workbook}::{worksheet} is missing columns: {column_names}',
    'extra_columns':     'Worksheet {workbook}::{worksheet} has extra columns: {column_names}',
    'too_few_rows':      'Worksheet {workbook}::{worksheet} has too few rows (min is {min_rows} and max is {max_rows})',
    'too_many_rows':     'Worksheet {workbook}::{worksheet} has too many rows (min is {min_rows} and max is {max_rows})',
}


class TestDocuments:
    def test_documents(self, dataset_path):
        # Build expected

        expected_documents = [Document(*args) for args in TEST_DATA]

        # Assert

        with Dataset(dataset_path) as dataset:
            documents = list(dataset.documents)
            assert documents == expected_documents

    def test_documents_with_empty_file(self, dataset_path):
        # Modify documents file

        document_path = dataset_path / TEST_FILE_NAME
        os.truncate(document_path, 0)

        # Assert

        with pytest.raises(ValueError) as excinfo:
            with Dataset(dataset_path) as dataset:
                pass

    def test_documents_with_missing_sheet(self, dataset_path):
        # Modify

        documents_path = dataset_path / TEST_FILE_NAME

        wb = load_workbook(documents_path)
        ws = wb[TEST_SHEET_NAME]
        ws.title = "Skittles"
        wb.save(documents_path)

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

    def test_documents_with_missing_columns(self, dataset_path):
        document_path = dataset_path / TEST_FILE_NAME

        with pd.ExcelWriter(document_path) as writer:
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

    def test_documents_with_extra_columns(self, dataset_path):
        document_path = dataset_path / TEST_FILE_NAME

        df = pd.read_excel(document_path, sheet_name=TEST_SHEET_NAME)

        with pd.ExcelWriter(document_path) as writer:
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

    def test_documents_with_extra_columns_ok(self, dataset_path):
        # Modify file

        document_path = dataset_path / TEST_FILE_NAME

        df = pd.read_excel(document_path, sheet_name=TEST_SHEET_NAME)

        with pd.ExcelWriter(document_path) as writer:
            df['CAT'] = ['Skittles']
            df.to_excel(writer, sheet_name=TEST_SHEET_NAME, index=False)

        # Build expected

        NEW_TEST_DATA = TEST_DATA.copy()
        NEW_TEST_DATA[0] = NEW_TEST_DATA[0] + (frozenset((('cat', 'Skittles'),)),)

        expected_documents = [Document(*args) for args in NEW_TEST_DATA]

        # Assert

        with Dataset(dataset_path, extra_columns_ok=True) as dataset:
            documents = list(dataset.documents)
            assert documents == expected_documents

    def test_documents_with_no_data(self, dataset_path):
        # Modify samples file

        document_path = dataset_path / TEST_FILE_NAME

        df = pd.read_excel(document_path, sheet_name=TEST_SHEET_NAME)

        with pd.ExcelWriter(document_path) as writer:
            df = df[0:0]
            df.to_excel(writer, sheet_name=TEST_SHEET_NAME, index=False)

        # Expected

        expected_error_msg_kwargs = {
            'workbook': TEST_FILE_NAME,
            'worksheet': TEST_SHEET_NAME,
            'min_rows': 1,
            'max_rows': 1,
        }

        # Assert

        with pytest.raises(IntegrityError) as excinfo:
            with Dataset(dataset_path) as dataset:
                pass

        assert excinfo.value.args[0] == ERROR_MESSAGES['too_few_rows'].format(**expected_error_msg_kwargs)

    def test_documents_with_too_much_data(self, dataset_path):
        # Modify samples file

        document_path = dataset_path / TEST_FILE_NAME

        df = pd.read_excel(document_path, sheet_name=TEST_SHEET_NAME)

        with pd.ExcelWriter(document_path) as writer:
            new_document = df.iloc[0]
            new_document['RECOMMENDED_CITATION'] = new_document['RECOMMENDED_CITATION'] + '-different'

            df = df.append(new_document, ignore_index=True)

            df.to_excel(writer, sheet_name=TEST_SHEET_NAME, index=False)

        # Expected

        expected_error_msg_kwargs = {
            'workbook': TEST_FILE_NAME,
            'worksheet': TEST_SHEET_NAME,
            'min_rows': 1,
            'max_rows': 1,
        }

        # Assert

        with pytest.raises(IntegrityError) as excinfo:
            with Dataset(dataset_path) as dataset:
                pass

        assert excinfo.value.args[0] == ERROR_MESSAGES['too_many_rows'].format(**expected_error_msg_kwargs)

    def test_documents_with_duplicate(self, dataset_path):
        assert True  # Not necessary since only one row is permitted
