from __future__ import annotations
import collections
from copy import deepcopy
import itertools
from pathlib import Path
from typing import Generator, Iterator

from geochem_dataset.excel import Dataset
from geochem_dataset.excel.dataclasses import Survey, Sample, Result
from geochem_dataset.excel.exceptions import (
    IntegrityError,
)

import attr
import numpy as np
import pandas as pd
import pytest

from helpers.utils import xlref, xlrowref, xlcolref

pd.options.display.max_columns = 99

ERROR_MESSAGES = {
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
    'result_type_missing':                     'Result type in cell {cell} of worksheet {workbook}::{worksheet} is missing'
}


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
        'sample_subsample_results_sets': [
            (SAMPLES[0], ('11TIAT001',), ('2.5Y 6/4', 'light yellowish brown', '7.256')),
            (SAMPLES[1], ('11TIAT024',), ('2.5Y 5/4', 'light olive brown', '22.173')),
        ],
        'metadata_types': ('Method', 'Threshold', 'Unit', 'Fraction_min', 'Fraction_max', 'Year', 'Lab_analysis'),
        'result_type_metadata_sets': [
            ('Soil_Munsell', ('SP64 Series X-Rite Spectrophotometer', '', '', '0', '2mm', '2013', 'GSC Sedimentology')),
            ('Colour_Description', ('SP64 Series X-Rite Spectrophotometer', '', '', '0', '2mm', '2013', 'GSC Sedimentology')),
            ('W_peb_bulk', ('laser particle size analyzer and Camsizer & Lecotrac LT100', '', 'pct', '0', '30cm', '2013', 'GSC Sedimentology')),
        ],
    },
    'BULK2': {
        'sample_subsample_results_sets': [
            (SAMPLES[2], ('12TIAT138',), ('2.5Y 6/4', 'light yellowish brown', '12.699')),
            (SAMPLES[3], ('12TIAT139',), ('2.5Y 5/4', 'light olive brown', '22.173')),
        ],
        'metadata_types': ('Method', 'Threshold', 'Unit', 'Fraction_min', 'Fraction_max', 'Year', 'Lab_analysis'),
        'result_type_metadata_sets': [
            ('Soil_Munsell', ('SP64 Series X-Rite Spectrophotometer', '', '', '0', '2mm', '2013', 'GSC Sedimentology')),
            ('Colour_Description', ('SP64 Series X-Rite Spectrophotometer', '', '', '0', '2mm', '2013', 'GSC Sedimentology')),
            ('W_peb_bulk', ('laser particle size analyzer and Camsizer & Lecotrac LT100', '', 'pct', '0', '30cm', '2013', 'GSC Sedimentology')),
        ],
    }
}




@attr.s
class BulkWorkbookData:
    worksheets: dict[str, BulkWorksheetData] = attr.ib(factory=list)

    @property
    def results(self) -> collections.Generator[Result]:
        for _, data in self.worksheets.items():
            for result in data.results:
                yield result

    def to_excel(self, path: Path) -> pd.DataFrame:
        with pd.ExcelWriter(path) as writer:
            for sheet_name, data in self.worksheets.items():
                df = data.to_dataframe()
                df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)

    @classmethod
    def from_dict(cls, data: dict) -> BulkWorkbookData:
        data = deepcopy(data)

        return BulkWorkbookData(worksheets={
            sheet_name: BulkWorksheetData(**sheet_data)
            for sheet_name, sheet_data in data.items()
        })

    def clear_subsamples(self):
        for _, data in self.worksheets.items():
            data.clear_subsamples()

    def clear_metadata_types(self):
        for _, data in self.worksheets.items():
            data.clear_metadata_types()

    def clear_result_types(self):
        for _, data in self.worksheets.items():
            data.clear_result_types()


@attr.s
class BulkWorksheetData:
    sample_subsample_results_sets: list[tuple(Sample, tuple[str, ...], tuple[str, ...])] = attr.ib(factory=list)
    metadata_types: tuple(str) = attr.ib(factory=tuple)
    result_type_metadata_sets: list[tuple(str, tuple(str, ...))] = attr.ib(factory=list)

    @property
    def results(self) -> collections.Generator[Result]:
        for sample, subsample, results in self.sample_subsample_results_sets:
            subsample = tuple(str(x).strip() for x in subsample)

            for result, (result_type, metadata) in zip(results, self.result_type_metadata_sets):
                metadata = frozenset(zip(self.metadata_types, metadata))
                metadata = frozenset((x, y) for x, y in metadata if y)

                yield Result(sample, subsample, result_type, metadata, result)

    def to_dataframe(self) -> pd.DataFrame:
        df = pd.DataFrame()

        # Headings/result types row

        row = ('SAMPLE',)

        num_subsample_columns = (
            len(self.sample_subsample_results_sets[0][1])
            if self.sample_subsample_results_sets
            else 1
        )

        for _ in range(num_subsample_columns):
            row += ('SUB' + row[-1],)

        row += ('METADATA_TYPE',)
        row += tuple(result_type for result_type, _ in self.result_type_metadata_sets)

        df = df.append(pd.Series(row), ignore_index=True)

        # Metadata rows

        num_subsample_columns = (
            len(self.sample_subsample_results_sets[0][1])
            if self.sample_subsample_results_sets
            else 1
        )

        for metadata_type_idx, metadata_type in enumerate(self.metadata_types):
            row = ('',)  # sample column
            row += ('',) * num_subsample_columns  # subsample columns
            row += (metadata_type,)
            row += tuple(
                metadata[metadata_type_idx]
                for _, metadata in self.result_type_metadata_sets
            )

            df = df.append(pd.Series(row), ignore_index=True)

        # Subsample/result rows

        for sample, subsample, results in self.sample_subsample_results_sets:
            row = (sample.name,)
            row += subsample
            row += ('',)  # metadata type column in subsample row is blank
            row += results

            df = df.append(pd.Series(row), ignore_index=True)

        return df

    def clear_subsamples(self):
        self.sample_subsample_results_sets = list()

    def clear_metadata_types(self):
        self.metadata_types = tuple()
        self.result_type_metadata_sets = [
            (result_type, tuple())
            for result_type, _ in self.result_type_metadata_sets
        ]

    def clear_result_types(self):
        self.result_type_metadata_sets = list()
        self.sample_subsample_results_sets = [
            (sample, subsample, tuple())
            for sample, subsample, _ in self.sample_subsample_results_sets
        ]




class TestBulk:
    def test(self, dataset_path):
        expected_data = BulkWorkbookData.from_dict(BULK_DATA)

        with Dataset(dataset_path) as dataset:
            assert set(dataset.analysis_bulk_results) == set(expected_data.results)

    def test_with_trailing_whitespace_on_subsample(self, dataset_path):
        # Modify

        expected_data = BulkWorkbookData.from_dict(BULK_DATA)

        for ws_data in expected_data.worksheets.values():
            ws_data.sample_subsample_results_sets = [
                (sample, tuple(f'{x} \t' for x in subsample), results)
                for sample, subsample, results in ws_data.sample_subsample_results_sets
            ]

        expected_data.to_excel(dataset_path / BULK_FILE_NAME)

        # Assert

        with Dataset(dataset_path) as dataset:
            assert set(dataset.analysis_bulk_results) == set(expected_data.results)

    def test_without_bulk_raises_on_access(self, dataset_path):
        # Modify

        bulk_path = dataset_path / BULK_FILE_NAME
        bulk_path.unlink()

        # Assert

        with Dataset(dataset_path) as dataset:
            with pytest.raises(AttributeError) as excinfo:
                dataset.analysis_bulk_results

    def test_with_deeper_subsample_levels(self, dataset_path):
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

        expected_results = convert_bulk_data_to_expected_results(new_bulk_data)

        # Assert

        with Dataset(dataset_path) as dataset:
            results = list(dataset.analysis_bulk_results)
            assert set(dataset.analysis_bulk_results) == set(expected_results)


class TestNoData:
    # Structure is valid. Just no data.

    # All combinations of axes to test cleared
    AXES_TO_CLEAR = list(itertools.chain(*list(itertools.combinations(('subsamples', 'metadata_types', 'result_types'), r) for r in range(1, 4))))

    @pytest.mark.parametrize('axes_to_clear', AXES_TO_CLEAR, ids=['_'.join(x) for x in AXES_TO_CLEAR])
    def test(self, dataset_path, axes_to_clear):
        data = BulkWorkbookData.from_dict(BULK_DATA)

        for axis_to_clear in axes_to_clear:
            getattr(data, f"clear_{axis_to_clear}")()

        path = dataset_path / BULK_FILE_NAME
        data.to_excel(path)

        expected_results = data.results

        with Dataset(dataset_path) as dataset:
            assert set(dataset.analysis_bulk_results) == set(expected_results)


class TestResultTypeErrors:
    @pytest.mark.parametrize("column_idx", [3, 4, 5])
    def test_with_missing_result_type(self, dataset_path, column_idx):
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

    def test_with_NA_as_result_type(self, dataset_path):
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

        expected_results = convert_bulk_data_to_expected_results(new_bulk_data)

        # Assert

        with Dataset(dataset_path) as dataset:
            results = list(dataset.analysis_bulk_results)
            assert set(results) == set(expected_results)

    def test_with_integer_as_sample_name(self, dataset_path):
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

        expected_results = convert_bulk_data_to_expected_results(new_bulk_data)

        # Assert

        with Dataset(dataset_path) as dataset:
            results = list(dataset.analysis_bulk_results)
            assert len(results) == len(expected_results)
            assert set(results) == set(expected_results)


class TestMissingHeadingErrors:
    def test_missing_sample_heading(self, dataset_path):
        # Modify bulk file

        bulk_path = dataset_path / BULK_FILE_NAME

        dfs = {
            sheet_name: pd.read_excel(bulk_path, header=None, sheet_name=sheet_name)
            for sheet_name in BULK_DATA
        }

        with pd.ExcelWriter(bulk_path) as writer:
            for sheet_name, df in dfs.items():
                df.iloc[0, 0] = 'INVALID SAMPLES HEADING'
                df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
                break

        # Build expected

        expected_error_values = {
            'workbook': BULK_FILE_NAME,
            'worksheet': list(dfs)[0],
            'cell': 'A1',
            'message': ERROR_MESSAGES['sample_heading_missing']
        }

        # Assert

        with pytest.raises(IntegrityError) as excinfo:
            with Dataset(dataset_path) as dataset:
                pass

        assert excinfo.value.workbook == expected_error_values['workbook']
        assert excinfo.value.worksheet == expected_error_values['worksheet']
        assert excinfo.value.cell == expected_error_values['cell']
        assert excinfo.value.message == expected_error_values['message']

    def test_missing_subsample_heading(self, dataset_path):
        # Modify bulk file

        bulk_path = dataset_path / BULK_FILE_NAME

        dfs = {
            sheet_name: pd.read_excel(bulk_path, header=None, sheet_name=sheet_name)
            for sheet_name in BULK_DATA
        }

        with pd.ExcelWriter(bulk_path) as writer:
            for sheet_name, df in dfs.items():
                df.iloc[0, 1] = 'INVALID SUBSAMPLE HEADING'
                df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
                break

        # Build expected

        expected_error_values = {
            'workbook': BULK_FILE_NAME,
            'worksheet': list(dfs)[0],
            'cell': 'B1',
            'message': ERROR_MESSAGES['subsample_heading_missing']
        }

        # Assert

        with pytest.raises(IntegrityError) as excinfo:
            with Dataset(dataset_path) as dataset:
                pass

        assert excinfo.value.workbook == expected_error_values['workbook']
        assert excinfo.value.worksheet == expected_error_values['worksheet']
        assert excinfo.value.cell == expected_error_values['cell']
        assert excinfo.value.message == expected_error_values['message']

    def test_missing_metadata_type_heading(self, dataset_path):
        # Modify bulk file

        bulk_path = dataset_path / BULK_FILE_NAME

        dfs = {
            sheet_name: pd.read_excel(bulk_path, header=None, sheet_name=sheet_name)
            for sheet_name in BULK_DATA
        }

        with pd.ExcelWriter(bulk_path) as writer:
            for sheet_name, df in dfs.items():
                df.iloc[0, 2] = 'INVALID METADATA TYPE HEADING'
                df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
                break

        # Build expected

        expected_error_values = {
            'workbook': BULK_FILE_NAME,
            'worksheet': list(dfs)[0],
            'cell': 'C1',
            'message': ERROR_MESSAGES['metadata_type_heading_missing']
        }

        # Assert

        with pytest.raises(IntegrityError) as excinfo:
            with Dataset(dataset_path) as dataset:
                pass

        assert excinfo.value.workbook == expected_error_values['workbook']
        assert excinfo.value.worksheet == expected_error_values['worksheet']
        assert excinfo.value.cell == expected_error_values['cell']
        assert excinfo.value.message == expected_error_values['message']


class TestEmptyRegionErrors:
    def test_with_region_left_of_metadata_types_not_empty(self, dataset_path):
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

        expected_error_values = {
            'workbook': BULK_FILE_NAME,
            'worksheet': list(dfs)[0],
            'cell': None,
            'message': ERROR_MESSAGES['region_left_of_metadata_types_not_empty']
        }

        # Assert

        with pytest.raises(IntegrityError) as excinfo:
            with Dataset(dataset_path) as dataset:
                pass

        assert excinfo.value.workbook == expected_error_values['workbook']
        assert excinfo.value.worksheet == expected_error_values['worksheet']
        assert excinfo.value.cell == expected_error_values['cell']
        assert excinfo.value.message == expected_error_values['message']

    def test_with_region_below_metadata_types_not_empty(self, dataset_path):
        assert False


class TestSampleSubsampleErrors:
    def test_with_one_value_of_subsample_missing(self, dataset_path):
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

    def test_with_all_values_of_subsample_missing(self, dataset_path):
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

    def test_with_non_existant_sample_value(self, dataset_path):
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

    def test_with_duplicate_subsmaple_in_same_worksheet(self, dataset_path):
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


class TestMetadataTypeErrors:
    def test_with_missing_metadata_type(self, dataset_path):
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


class TestDuplicateErrors:
    def test_with_duplicate_result_type_metadata_set_in_same_worksheet(self, dataset_path):
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

    def test_with_duplicate_subsample_result_type_metadata_set_in_different_worksheets(self, dataset_path):
        # Modify bulk file

        bulk_path = dataset_path / BULK_FILE_NAME

        dfs = {
            sheet_name: pd.read_excel(bulk_path, header=None, sheet_name=sheet_name)
            for sheet_name in BULK_DATA
        }

        sheet_names = list(dfs.keys())
        dfs[sheet_names[1]] = dfs[sheet_names[0]]

        with pd.ExcelWriter(bulk_path) as writer:
            for sheet_name, df in dfs.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)

        # Build expected

        expected_error_message_kwargs = {
            'workbook': BULK_FILE_NAME,
            'worksheet': list(dfs)[0],
            'column': xlcolref(6),
        }

        with pytest.raises(IntegrityError) as excinfo:
            with Dataset(dataset_path) as dataset:
                pass

        assert excinfo.value.args[0] == ERROR_MESSAGES['subsample_result_type_metadata_pair_duplicate'].format(**expected_error_message_kwargs)

    def test_with_duplicate_metadata_type_in_same_worksheet(self, dataset_path):
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
