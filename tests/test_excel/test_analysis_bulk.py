from copy import deepcopy

from geochem_dataset.excel import Dataset
from geochem_dataset.excel.dataclasses import Survey, Sample, Result
from geochem_dataset.excel.exceptions import (
    IntegrityError,
)

import numpy as np
import pandas as pd
import pytest

from helpers.utils import xlref, xlrowref, xlcolref


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
"""

SAMPLES_FILE_NAME = 'SAMPLES.xlsx'
SAMPLES_SHEET_NAME = 'SAMPLES'

SURVEYS = [
    Survey('2011, Till sampling survey, Hall Peninsula. Canada-Nunavut Geoscience Office', 'Canada-Nunavut Geoscience Office', 2011, 2013, 'Tremblay, Tommy', 'A test description', 1000),
]

SAMPLES = [
    Sample(SURVEYS[0], '11TIAT001', '11TIAT001A', '11TIAT001A01', None, None, 64.010103, -67.351092, None, None, None, None, None, 'Till', None),
    Sample(SURVEYS[0], '11TIAT024', '11TIAT024A', '11TIAT024A01', None, None, 64.472825, -67.721319, None, None, None, None, None, 'Till', None),
    Sample(SURVEYS[0], '12TIAT138', '12TIAT138A', '12TIAT138A01', None, None, 64.209300, -67.011316, None, None, None, None, None, 'Till', None),
    Sample(SURVEYS[0], '12TIAT139', '12TIAT139A', '12TIAT139A01', None, None, 64.334217, -67.087329, None, None, None, None, None, 'Till', None),
]

BULK_FILE_NAME = 'BULK.xlsx'
BULK_DATA = {
    'BULK1': {
        'subsamples': [
            (SAMPLES[0], '11TIAT001'),
            (SAMPLES[1], '11TIAT024'),
        ],
        'result_types': [
            'Soil_Munsell', 'Colour_Description', 'W_peb_bulk'
        ],
        'metadata_types': [
            'Method', 'Threshold', 'Unit', 'Fraction_min', 'Fraction_max', 'Year', 'Lab_analysis'
        ],
        'metadata_values': [
            ('SP64 Series X-Rite Spectrophotometer', None, None, '0', '2mm', '2013', 'GSC Sedimentology'),
            ('SP64 Series X-Rite Spectrophotometer', None, None, '0', '2mm', '2013', 'GSC Sedimentology'),
            ('laser particle size analyzer and Camsizer & Lecotrac LT100', None, 'pct', '0', '30cm', '2013', 'GSC Sedimentology'),
        ],
        'results': [
            # subsample_idx, result_type_idx, metadata_values_idx, result
            (0, 0, 0, '2.5Y 6/4'),
            (0, 1, 1, 'light yellowish brown'),
            (0, 2, 2, '7.256'),
            (1, 0, 0, '10YR 5/4'),
            (1, 1, 1, 'yellowish brown'),
            (1, 2, 2, '33.538'),
        ]
    },
    'BULK2': {
        'subsamples': [
            (SAMPLES[2], '12TIAT138'),
            (SAMPLES[3], '12TIAT139'),
        ],
        'result_types': [
            'Soil_Munsell', 'Colour_Description', 'W_peb_bulk'
        ],
        'metadata_types': [
            'Method', 'Threshold', 'Unit', 'Fraction_min', 'Fraction_max', 'Year', 'Lab_analysis'
        ],
        'metadata_values': [
            ('SP64 Series X-Rite Spectrophotometer', None, None, '0', '2mm', '2013', 'GSC Sedimentology'),
            ('SP64 Series X-Rite Spectrophotometer', None, None, '0', '2mm', '2013', 'GSC Sedimentology'),
            ('laser particle size analyzer and Camsizer & Lecotrac LT100', None, 'pct', '0', '30cm', '2013', 'GSC Sedimentology'),
        ],
        'results': [
            # subsample_idx, result_type_idx, metadata_values_idx, result
            (0, 0, 0, '2.5Y 6/4'),
            (0, 1, 1, 'light yellowish brown'),
            (0, 2, 2, '12.699'),
            (1, 0, 0, '2.5Y 5/4'),
            (1, 1, 1, 'light olive brown'),
            (1, 2, 2, '22.173'),
        ]
    }
}

ERROR_MESSAGES = {
    'sample_heading_missing':                  'Cell {cell} of worksheet {workbook}::{worksheet} must be SAMPLE',
    'subsample_heading_missing':               'Cell {cell} of worksheet {workbook}::{worksheet} must be SUBSAMPLE',
    'metadata_type_heading_missing':           'Cell {cell} of worksheet {workbook}::{worksheet} must be METADATA_TYPE',
    'region_left_of_metadata_types_not_empty': 'Region left of metadata types in worksheet {workbook}::{worksheet} is not empty',
    'metadata_type_missing':                   'Metadata type is missing in cell {cell} of worksheet {workbook}::{worksheet}',
    'metadata_type_duplicate':                 'Metadata type in cell {cell} of worksheet {workbook}::{worksheet} is a duplicate',
    'result_type_metadata_pair_duplicate':     'Result type-metadata pair in column {column} of worksheet {workbook}::{worksheet} is a duplicate',
    'subsample_values_missing':                'Missing value(s) for subsample in row {row} of worksheet {workbook}::{worksheet}',
    'sample_does_not_exist':                   'Sample in cell {cell} of worksheet {workbook}::{worksheet} does not exist',
    'subsample_duplicate':                     'Subsample in row {row} of worksheet {workbook}::{worksheet} is a duplicate',
    'result_type_missing':                     'Result type in cell {cell} of worksheet {workbook}::{worksheet} is missing'
}


def build_expected_results(data):
    expected_results = []

    for sheet_name in data:
        subsamples = data[sheet_name]['subsamples']
        result_types = data[sheet_name]['result_types']
        metadata_types = data[sheet_name]['metadata_types']
        metadata_value_tuples = data[sheet_name]['metadata_values']

        for subsample_idx, result_type_idx, metadata_values_idx, result_value in data[sheet_name]['results']:
            sample = subsamples[subsample_idx][0]
            subsample = tuple(subsamples[subsample_idx][1:])
            result_type = result_types[result_type_idx]

            metadata_values = [] if metadata_values_idx is None else metadata_value_tuples[metadata_values_idx]
            metadata = frozenset(x for x in zip(metadata_types, metadata_values) if x[1] is not None)

            result = Result(sample, subsample, result_type, metadata, result_value)

            expected_results.append(result)

    return expected_results


class TestBulk:
    def test_bulk(self, dataset_path):
        # Build expected

        expected_results = build_expected_results(BULK_DATA)

        # Assert

        with Dataset(dataset_path) as dataset:
            results = list(dataset.analysis_bulk_results)
            assert set(dataset.analysis_bulk_results) == set(expected_results)

    def test_bulk_with_spaces_at_end_of_subsample(self, dataset_path):
        # Modify bulk file

        bulk_path = dataset_path / BULK_FILE_NAME

        dfs = {
            sheet_name: pd.read_excel(bulk_path, header=None, sheet_name=sheet_name)
            for sheet_name in BULK_DATA
        }

        with pd.ExcelWriter(bulk_path) as writer:
            for sheet_name, df in dfs.items():
                df.iloc[8, 0] = df.iloc[8, 0] + ' '  # SAMPLE column
                df.iloc[8, 1] = df.iloc[8, 1] + ' '  # SUBSAMPLE column
                df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)

        # Build expected

        expected_results = build_expected_results(BULK_DATA)

        # Assert

        with Dataset(dataset_path) as dataset:
            results = list(dataset.analysis_bulk_results)
            assert set(dataset.analysis_bulk_results) == set(expected_results)

    def test_bulk_without_bulk(self, dataset_path):
        # Modify

        bulk_path = dataset_path / BULK_FILE_NAME
        bulk_path.unlink()

        # Assert

        with Dataset(dataset_path) as dataset:
            with pytest.raises(AttributeError) as excinfo:
                dataset.analysis_bulk_results

    # Test with no items on various combinations of axes

    def test_bulk_with_no_subsamples(self, dataset_path):
        # Modify file

        bulk_path = dataset_path / BULK_FILE_NAME

        dfs = {
            sheet_name: pd.read_excel(bulk_path, header=None, sheet_name=sheet_name)
            for sheet_name in BULK_DATA
        }

        with pd.ExcelWriter(bulk_path) as writer:
            for sheet_name, df in dfs.items():
                df = df.iloc[:8, :]  # Omit all subsample rows
                df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)

        # Build expected

        new_bulk_data = deepcopy(BULK_DATA)

        for sheet_name in new_bulk_data:
            new_bulk_data[sheet_name]['subsamples'] = []
            new_bulk_data[sheet_name]['results'] = []

        expected_results = build_expected_results(new_bulk_data)

        # Assert

        with Dataset(dataset_path) as dataset:
            results = list(dataset.analysis_bulk_results)
            assert set(dataset.analysis_bulk_results) == set(expected_results)

    def test_bulk_with_no_metadata_types(self, dataset_path):
        # Modify bulk file

        bulk_path = dataset_path / BULK_FILE_NAME

        dfs = {
            sheet_name: pd.read_excel(bulk_path, header=None, sheet_name=sheet_name)
            for sheet_name in BULK_DATA
        }

        with pd.ExcelWriter(bulk_path) as writer:
            for sheet_name, df in dfs.items():
                df = df.iloc[[0, 8, 9], :]  # Omit all metadata type rows
                df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)

        # Build expected results

        new_bulk_data = deepcopy(BULK_DATA)

        for sheet_name in new_bulk_data:
            new_bulk_data[sheet_name]['metadata_types'] = []
            new_bulk_data[sheet_name]['metadata_values'] = []

            for idx, result in enumerate(new_bulk_data[sheet_name]['results']):
                result = list(result)
                result[2] = None
                new_bulk_data[sheet_name]['results'][idx] = result

        expected_results = build_expected_results(new_bulk_data)

        # Assert

        with Dataset(dataset_path) as dataset:
            results = list(dataset.analysis_bulk_results)
            assert results == expected_results

    def test_bulk_with_no_result_types(self, dataset_path):
        # Modify bulk file

        bulk_path = dataset_path / BULK_FILE_NAME

        dfs = {
            sheet_name: pd.read_excel(bulk_path, header=None, sheet_name=sheet_name)
            for sheet_name in BULK_DATA
        }

        with pd.ExcelWriter(bulk_path) as writer:
            for sheet_name, df in dfs.items():
                df = df.iloc[:, :3]  # Omit all subsample rows
                df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)

        # Build expected results

        new_bulk_data = deepcopy(BULK_DATA)

        for sheet_name in new_bulk_data:
            new_bulk_data[sheet_name]['result_types'] = []
            new_bulk_data[sheet_name]['results'] = []

        expected_results = build_expected_results(new_bulk_data)

        # Assert

        with Dataset(dataset_path) as dataset:
            results = list(dataset.analysis_bulk_results)
            assert set(dataset.analysis_bulk_results) == set(expected_results)

    def test_bulk_with_no_subsamples_and_metadata_types(self, dataset_path):
        # Modify bulk file

        bulk_path = dataset_path / BULK_FILE_NAME

        dfs = {
            sheet_name: pd.read_excel(bulk_path, header=None, sheet_name=sheet_name)
            for sheet_name in BULK_DATA
        }

        with pd.ExcelWriter(bulk_path) as writer:
            for sheet_name, df in dfs.items():
                df = pd.DataFrame([df.iloc[0]], columns=list(range(len(df.iloc[0]))))
                df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)

        # Build expected results

        new_bulk_data = deepcopy(BULK_DATA)

        for sheet_name in new_bulk_data:
            new_bulk_data[sheet_name]['subsamples'] = []
            new_bulk_data[sheet_name]['metadata_types'] = []
            new_bulk_data[sheet_name]['results'] = []

        expected_results = build_expected_results(new_bulk_data)

        # Assert

        with Dataset(dataset_path) as dataset:
            results = list(dataset.analysis_bulk_results)
            assert set(dataset.analysis_bulk_results) == set(expected_results)

    def test_bulk_with_no_subsamples_and_result_types(self, dataset_path):
        # Modify bulk file

        bulk_path = dataset_path / BULK_FILE_NAME

        dfs = {
            sheet_name: pd.read_excel(bulk_path, header=None, sheet_name=sheet_name)
            for sheet_name in BULK_DATA
        }

        with pd.ExcelWriter(bulk_path) as writer:
            for sheet_name, df in dfs.items():
                df = df.iloc[:8, :3]
                df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)

        # Build expected results

        new_bulk_data = deepcopy(BULK_DATA)

        for sheet_name in new_bulk_data:
            new_bulk_data[sheet_name]['subsamples'] = []
            new_bulk_data[sheet_name]['result_types'] = []
            new_bulk_data[sheet_name]['results'] = []

        expected_results = build_expected_results(new_bulk_data)

        # Assert

        with Dataset(dataset_path) as dataset:
            results = list(dataset.analysis_bulk_results)
            assert set(dataset.analysis_bulk_results) == set(expected_results)

    def test_bulk_with_no_metadata_types_and_result_types(self, dataset_path):
        # Modify bulk file

        bulk_path = dataset_path / BULK_FILE_NAME

        dfs = {
            sheet_name: pd.read_excel(bulk_path, header=None, sheet_name=sheet_name)
            for sheet_name in BULK_DATA
        }

        with pd.ExcelWriter(bulk_path) as writer:
            for sheet_name, df in dfs.items():
                df = df.iloc[[0, 8, 9], :3]
                df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)

        # Build expected results

        new_bulk_data = deepcopy(BULK_DATA)

        for sheet_name in new_bulk_data:
            new_bulk_data[sheet_name]['metadata_types'] = []
            new_bulk_data[sheet_name]['result_types'] = []
            new_bulk_data[sheet_name]['results'] = []

        expected_results = build_expected_results(new_bulk_data)

        # Assert

        with Dataset(dataset_path) as dataset:
            results = list(dataset.analysis_bulk_results)
            assert set(dataset.analysis_bulk_results) == set(expected_results)

    def test_bulk_with_no_subsamples_metadata_types_and_result_types(self, dataset_path):
        # Modify bulk file

        bulk_path = dataset_path / BULK_FILE_NAME

        dfs = {
            sheet_name: pd.read_excel(bulk_path, header=None, sheet_name=sheet_name)
            for sheet_name in BULK_DATA
        }

        with pd.ExcelWriter(bulk_path) as writer:
            for sheet_name, df in dfs.items():
                df = pd.DataFrame([df.iloc[0, :3]], columns=list(range(len(df.iloc[0, :3]))))
                df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)

        # Build expected results

        new_bulk_data = deepcopy(BULK_DATA)

        for sheet_name in new_bulk_data:
            new_bulk_data[sheet_name]['subsamples'] = []
            new_bulk_data[sheet_name]['metadata_types'] = []
            new_bulk_data[sheet_name]['result_types'] = []
            new_bulk_data[sheet_name]['results'] = []

        expected_results = build_expected_results(new_bulk_data)

        # Assert

        with Dataset(dataset_path) as dataset:
            results = list(dataset.analysis_bulk_results)
            assert set(dataset.analysis_bulk_results) == set(expected_results)

    # Test headings

    def test_bulk_with_missing_sample_heading(self, dataset_path):
        # Modify bulk file

        bulk_path = dataset_path / BULK_FILE_NAME

        dfs = {
            sheet_name: pd.read_excel(bulk_path, header=None, sheet_name=sheet_name)
            for sheet_name in BULK_DATA
        }

        with pd.ExcelWriter(bulk_path) as writer:
            for sheet_name, df in dfs.items():
                df.iloc[0, 0] = 'SKITTLES'
                df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
                break

        # Build expected

        expected_error_msg_kwargs = {
            'workbook': BULK_FILE_NAME,
            'worksheet': list(dfs)[0],
            'cell': 'A1',
        }

        # Assert

        with pytest.raises(IntegrityError) as excinfo:
            with Dataset(dataset_path) as dataset:
                pass

        assert excinfo.value.args[0] == ERROR_MESSAGES['sample_heading_missing'].format(**expected_error_msg_kwargs)

    def test_bulk_with_missing_subsample_heading(self, dataset_path):
        # Modify bulk file

        bulk_path = dataset_path / BULK_FILE_NAME

        dfs = {
            sheet_name: pd.read_excel(bulk_path, header=None, sheet_name=sheet_name)
            for sheet_name in BULK_DATA
        }

        with pd.ExcelWriter(bulk_path) as writer:
            for sheet_name, df in dfs.items():
                df.iloc[0, 1] = 'SKITTLES'
                df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
                break

        # Build expected

        expected_error_msg_kwargs = {
            'workbook': BULK_FILE_NAME,
            'worksheet': list(dfs)[0],
            'cell': 'B1',
        }

        # Assert

        with pytest.raises(IntegrityError) as excinfo:
            with Dataset(dataset_path) as dataset:
                pass

        assert excinfo.value.args[0] == ERROR_MESSAGES['subsample_heading_missing'].format(**expected_error_msg_kwargs)

    def test_bulk_with_missing_metadata_type_heading(self, dataset_path):
        # Modify bulk file

        bulk_path = dataset_path / BULK_FILE_NAME

        dfs = {
            sheet_name: pd.read_excel(bulk_path, header=None, sheet_name=sheet_name)
            for sheet_name in BULK_DATA
        }

        with pd.ExcelWriter(bulk_path) as writer:
            for sheet_name, df in dfs.items():
                df.iloc[0, 2] = 'SKITTLES'
                df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
                break

        # Build expected

        expected_error_msg_kwargs = {
            'workbook': BULK_FILE_NAME,
            'worksheet': list(dfs)[0],
            'cell': 'C1',
        }

        # Assert

        with pytest.raises(IntegrityError) as excinfo:
            with Dataset(dataset_path) as dataset:
                pass

        assert excinfo.value.args[0] == ERROR_MESSAGES['metadata_type_heading_missing'].format(**expected_error_msg_kwargs)

    def test_bulk_with_only_subsample_columns(self, dataset_path):
        # Modify bulk file

        bulk_path = dataset_path / BULK_FILE_NAME

        dfs = {
            sheet_name: pd.read_excel(bulk_path, header=None, sheet_name=sheet_name)
            for sheet_name in BULK_DATA
        }

        with pd.ExcelWriter(bulk_path) as writer:
            for sheet_name, df in dfs.items():
                df = df.iloc[:, :2]
                df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
                break

        # Build expected

        expected_error_msg_kwargs = {
            'workbook': BULK_FILE_NAME,
            'worksheet': list(dfs)[0],
            'cell': 'C1',
        }

        # Assert

        with pytest.raises(IntegrityError) as excinfo:
            with Dataset(dataset_path) as dataset:
                pass

        assert excinfo.value.args[0] == ERROR_MESSAGES['metadata_type_heading_missing'].format(**expected_error_msg_kwargs)

    # Test empty regions

    def test_bulk_with_region_left_of_metadata_types_not_empty(self, dataset_path):
        # Modify bulk file

        bulk_path = dataset_path / BULK_FILE_NAME

        dfs = {
            sheet_name: pd.read_excel(bulk_path, header=None, sheet_name=sheet_name)
            for sheet_name in BULK_DATA
        }

        with pd.ExcelWriter(bulk_path) as writer:
            for sheet_name, df in dfs.items():
                df.iloc[3, 0] = 'SKITTLES'
                df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
                break

        # Expected

        expected_error_msg_kwargs = {
            'workbook': BULK_FILE_NAME,
            'worksheet': list(dfs)[0],
        }

        # Assert

        with pytest.raises(IntegrityError) as excinfo:
            with Dataset(dataset_path) as dataset:
                pass

        assert excinfo.value.args[0] == ERROR_MESSAGES['region_left_of_metadata_types_not_empty'].format(**expected_error_msg_kwargs)

    # Test metadata types

    def test_bulk_with_missing_metadata_type(self, dataset_path):
        # Modify bulk file

        bulk_path = dataset_path / BULK_FILE_NAME

        dfs = {
            sheet_name: pd.read_excel(bulk_path, header=None, sheet_name=sheet_name)
            for sheet_name in BULK_DATA
        }

        with pd.ExcelWriter(bulk_path) as writer:
            for sheet_name, df in dfs.items():
                df.iloc[3, 2] = np.NaN
                df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
                break

        # Build expected

        expected_error_msg_kwargs = {
            'workbook': BULK_FILE_NAME,
            'worksheet': list(dfs)[0],
            'cell': 'C4',
        }

        # Assert

        with pytest.raises(IntegrityError) as excinfo:
            with Dataset(dataset_path) as dataset:
                pass

        assert excinfo.value.args[0] == ERROR_MESSAGES['metadata_type_missing'].format(**expected_error_msg_kwargs)

    def test_bulk_with_duplicate_metadata_type(self, dataset_path):
        # Modify bulk file

        bulk_path = dataset_path / BULK_FILE_NAME

        dfs = {
            sheet_name: pd.read_excel(bulk_path, header=None, sheet_name=sheet_name)
            for sheet_name in BULK_DATA
        }

        with pd.ExcelWriter(bulk_path) as writer:
            for sheet_name, df in dfs.items():
                df.iloc[4, 2] = df.iloc[3, 2]
                df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
                break

        # Build expected

        expected_error_msg_kwargs = {
            'workbook': BULK_FILE_NAME,
            'worksheet': list(dfs)[0],
            'cell': 'C5',
        }

        # Assert

        with pytest.raises(IntegrityError) as excinfo:
            with Dataset(dataset_path) as dataset:
                pass

        assert excinfo.value.args[0] == ERROR_MESSAGES['metadata_type_duplicate'].format(**expected_error_msg_kwargs)

    def test_bulk_with_region_below_metadata_types_not_empty(self, dataset_path):
        pass  # This will never occur because metadata types are parsed before samples.

    # Test subsamples

    def test_bulk_with_one_value_of_subsample_missing(self, dataset_path):
        # Modify bulk file

        bulk_path = dataset_path / BULK_FILE_NAME

        dfs = {
            sheet_name: pd.read_excel(bulk_path, header=None, sheet_name=sheet_name)
            for sheet_name in BULK_DATA
        }

        with pd.ExcelWriter(bulk_path) as writer:
            for sheet_name, df in dfs.items():
                df.iloc[8, 0] = np.NaN
                df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
                break

        # Build expected

        expected_error_msg_kwargs = {
            'workbook': BULK_FILE_NAME,
            'worksheet': list(dfs)[0],
            'row': 9,
        }

        # Assert

        with pytest.raises(IntegrityError) as excinfo:
            with Dataset(dataset_path) as dataset:
                pass

        assert excinfo.value.args[0] == ERROR_MESSAGES['subsample_values_missing'].format(**expected_error_msg_kwargs)

    def test_bulk_with_all_values_of_subsample_missing(self, dataset_path):
        # Modify bulk file

        bulk_path = dataset_path / BULK_FILE_NAME

        dfs = {
            sheet_name: pd.read_excel(bulk_path, header=None, sheet_name=sheet_name)
            for sheet_name in BULK_DATA
        }

        with pd.ExcelWriter(bulk_path) as writer:
            for sheet_name, df in dfs.items():
                df.iloc[9, 0] = np.NaN
                df.iloc[9, 1] = np.NaN
                df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
                break

         # Build expected

        expected_error_msg_kwargs = {
            'workbook': BULK_FILE_NAME,
            'worksheet': list(dfs)[0],
            'row': 10,
        }

        # Assert

        with pytest.raises(IntegrityError) as excinfo:
            with Dataset(dataset_path) as dataset:
                pass

        assert excinfo.value.args[0] == ERROR_MESSAGES['subsample_values_missing'].format(**expected_error_msg_kwargs)

    def test_bulk_with_non_existant_sample_value(self, dataset_path):
        # Modify bulk file

        bulk_path = dataset_path / BULK_FILE_NAME

        dfs = {
            sheet_name: pd.read_excel(bulk_path, header=None, sheet_name=sheet_name)
            for sheet_name in BULK_DATA
        }

        with pd.ExcelWriter(bulk_path) as writer:
            for sheet_name, df in dfs.items():
                df.iloc[8, 0] = 'SKITTLES'
                df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
                break

        # Build expected

        expected_error_msg_kwargs = {
            'workbook': BULK_FILE_NAME,
            'worksheet': list(dfs)[0],
            'cell': xlref(8, 0)
        }

        # Assert

        with pytest.raises(IntegrityError) as excinfo:
            with Dataset(dataset_path) as dataset:
                pass

        assert excinfo.value.args[0] == ERROR_MESSAGES['sample_does_not_exist'].format(**expected_error_msg_kwargs)

    def test_bulk_with_duplicate_subsmaple(self, dataset_path):
        # Modify bulk file

        bulk_path = dataset_path / BULK_FILE_NAME

        dfs = {
            sheet_name: pd.read_excel(bulk_path, header=None, sheet_name=sheet_name)
            for sheet_name in BULK_DATA
        }

        with pd.ExcelWriter(bulk_path) as writer:
            for sheet_name, df in dfs.items():
                df = df.append(df.iloc[9])
                df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
                break

        # Build expected

        expected_error_msg_kwargs = {
            'workbook': BULK_FILE_NAME,
            'worksheet': list(dfs)[0],
            'row': xlrowref(10)
        }

        # Assert

        with pytest.raises(IntegrityError) as excinfo:
            with Dataset(dataset_path) as dataset:
                pass

        assert excinfo.value.args[0] == ERROR_MESSAGES['subsample_duplicate'].format(**expected_error_msg_kwargs)

    def test_bulk_with_deeper_subsample_levels(self, dataset_path):
        # Modify bulk file

        bulk_path = dataset_path / BULK_FILE_NAME

        dfs = {
            sheet_name: pd.read_excel(bulk_path, header=None, sheet_name=sheet_name)
            for sheet_name in BULK_DATA
        }

        with pd.ExcelWriter(bulk_path) as writer:
            for sheet_name, df in dfs.items():
                df.insert(loc=2, column='2-new', value=df[1])
                df.columns = range(len(df.columns))
                df[2][0] = 'SUBSUBSAMPLE'
                df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)

        # Build expected

        new_bulk_data = deepcopy(BULK_DATA)

        for sheet_name in new_bulk_data:
            new_bulk_data[sheet_name]['subsamples'] =  [
                (s1, s2, s2)
                for s1, s2 in new_bulk_data[sheet_name]['subsamples']
            ]

        expected_results = build_expected_results(new_bulk_data)

        # Assert

        with Dataset(dataset_path) as dataset:
            results = list(dataset.analysis_bulk_results)
            assert set(dataset.analysis_bulk_results) == set(expected_results)

    # Test result types

    @pytest.mark.parametrize("column_idx", [3, 4, 5])
    def test_bulk_with_missing_result_type(self, dataset_path, column_idx):
        # Modify bulk file

        bulk_path = dataset_path / BULK_FILE_NAME

        dfs = {
            sheet_name: pd.read_excel(bulk_path, header=None, sheet_name=sheet_name)
            for sheet_name in BULK_DATA
        }

        with pd.ExcelWriter(bulk_path) as writer:
            for sheet_name, df in dfs.items():
                df.iloc[0, column_idx] = np.NaN
                df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
                break

        # Build expected

        expected_error_msg_kwargs = {
            'workbook': BULK_FILE_NAME,
            'worksheet': list(dfs)[0],
            'cell': xlref(0, column_idx)
        }

        # Assert

        with pytest.raises(IntegrityError) as excinfo:
            with Dataset(dataset_path) as dataset:
                pass

        assert excinfo.value.args[0] == ERROR_MESSAGES['result_type_missing'].format(**expected_error_msg_kwargs)

    def test_bulk_with_duplicate_result_type_metadata_pair(self, dataset_path):
        # Modify bulk file

        bulk_path = dataset_path / BULK_FILE_NAME

        dfs = {
            sheet_name: pd.read_excel(bulk_path, header=None, sheet_name=sheet_name)
            for sheet_name in BULK_DATA
        }

        with pd.ExcelWriter(bulk_path) as writer:
            for sheet_name, df in dfs.items():
                df[6] = df[5]
                df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
                break

        # Build expected

        expected_error_message_kwargs = {
            'workbook': BULK_FILE_NAME,
            'worksheet': list(dfs)[0],
            'column': xlcolref(6),
        }

        # Assert

        with pytest.raises(IntegrityError) as excinfo:
            with Dataset(dataset_path) as dataset:
                pass

        assert excinfo.value.args[0] == ERROR_MESSAGES['result_type_metadata_pair_duplicate'].format(**expected_error_message_kwargs)

    def test_bulk_with_NA_as_result_type(self, dataset_path):
        # Modify bulk file

        bulk_path = dataset_path / BULK_FILE_NAME

        dfs = {
            sheet_name: pd.read_excel(bulk_path, header=None, sheet_name=sheet_name)
            for sheet_name in BULK_DATA
        }

        with pd.ExcelWriter(bulk_path) as writer:
            for sheet_name, df in dfs.items():
                df.iloc[0, 4] = 'NA'
                df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)

        # Build expected

        new_bulk_data = deepcopy(BULK_DATA)

        for sheet_name in new_bulk_data:
            new_bulk_data[sheet_name]['result_types'][1] = 'NA'

        expected_results = build_expected_results(new_bulk_data)

        # Assert

        with Dataset(dataset_path) as dataset:
            results = list(dataset.analysis_bulk_results)
            assert set(results) == set(expected_results)

    def test_bulk_with_integer_as_sample_name(self, dataset_path):
        # Modify samples file

        samples_path = dataset_path / SAMPLES_FILE_NAME

        df = pd.read_excel(samples_path, sheet_name=SAMPLES_SHEET_NAME)

        with pd.ExcelWriter(samples_path) as writer:
            df.iloc[0, 3] = 256
            df.to_excel(writer, sheet_name=SAMPLES_SHEET_NAME, index=False)

        # Modify bulk file

        bulk_path = dataset_path / BULK_FILE_NAME

        dfs = {
            sheet_name: pd.read_excel(bulk_path, header=None, sheet_name=sheet_name)
            for sheet_name in BULK_DATA
        }

        with pd.ExcelWriter(bulk_path) as writer:
            for sheet_name, df in dfs.items():
                if sheet_name == 'BULK1':
                    df.iloc[8, 0] = 256
                df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)

        # Build expected

        new_bulk_data = deepcopy(BULK_DATA)

        for sheet_name in new_bulk_data:
            new_bulk_data[sheet_name]['subsamples'][0] = (
                Sample(SURVEYS[0], '11TIAT001', '11TIAT001A', '256', None, None, 64.010103, -67.351092, None, None, None, None, None, 'Till', None),
                '11TIAT001'
            )
            break

        expected_results = build_expected_results(new_bulk_data)

        # Assert

        with Dataset(dataset_path) as dataset:
            results = list(dataset.analysis_bulk_results)
            assert len(results) == len(expected_results)
            assert set(results) == set(expected_results)
