import itertools
import re
from typing import Iterable

from geochem_dataset.excel import Dataset
from geochem_dataset.excel.exceptions import IntegrityError
import pandas as pd
import pytest

from tests.helpers.utils import xlref


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

    'missing_result_type':                     'Missing result type'
}

def list_of_subsets(items: Iterable) -> list:
    """Return all combinations of subsets of given set of items. Different sizes of subsets will be
    returned, starting with just one item and ending with all items."""

    return list(itertools.chain(*list(itertools.combinations(items, r) for r in range(1, len(items) + 1))))


class TestNoBulkFile:
    def test_raises(self, test_dataset_path, test_dataset_data):
        test_dataset_data.to_excel(test_dataset_path)

        bulk_wb_path = test_dataset_path / 'BULK.xlsx'
        bulk_wb_path.unlink()

        with Dataset(test_dataset_path) as dataset:
            with pytest.raises(AttributeError):
                dataset.bulk


class TestSubsamples:
    def test_raises_with_non_existant_sample_value(self, test_dataset_path, test_dataset_data):
        mutations = {
            'BULK.xlsx': {
                'BULK1': {
                    'A9': 'Duchess'
                }
            }
        }

        test_dataset_data.to_excel(test_dataset_path, mutations)

        with pytest.raises(IntegrityError) as excinfo:
            with Dataset(test_dataset_path) as dataset:
                pass

        assert excinfo.value.workbook == 'BULK.xlsx'
        assert excinfo.value.worksheet == 'BULK1'
        assert excinfo.value.message == 'Sample value "Duchess" of subsample on row 9 does not exist in "SAMPLES.xlsx"'

    @pytest.mark.parametrize('cell_to_clear', ['A9', 'B9', 'A10', 'B10'])
    def test_raises_with_missing_sample_value(self, test_dataset_path, test_dataset_data, cell_to_clear):
        mutations = {
            'BULK.xlsx': {
                'BULK1': {
                    cell_to_clear: ''
                }
            }
        }

        test_dataset_data.to_excel(test_dataset_path, mutations)

        with pytest.raises(IntegrityError) as excinfo:
            with Dataset(test_dataset_path) as dataset:
                pass

        assert excinfo.value.workbook == 'BULK.xlsx'
        assert excinfo.value.worksheet == 'BULK1'

        row_xl_idx = re.match('^([A-Z]+)([0-9]+)$', cell_to_clear).group(2)
        assert excinfo.value.message == f'Missing value(s) for subsample on row {row_xl_idx}'

    def test_raises_with_duplicate_subsmaple_in_same_worksheet(self, test_dataset_path, test_dataset_data):
        existing_subsample_row = test_dataset_data.workbooks['BULK.xlsx'].worksheets['BULK1'].data['subsample_results_sets'][-1]
        test_dataset_data.workbooks['BULK.xlsx'].worksheets['BULK1'].data['subsample_results_sets'].append(existing_subsample_row)

        test_dataset_data.to_excel(test_dataset_path)

        with pytest.raises(IntegrityError) as excinfo:
            with Dataset(test_dataset_path) as dataset:
                pass

        assert excinfo.value.workbook == 'BULK.xlsx'
        assert excinfo.value.worksheet == 'BULK1'

        duplicate_of_row_xl_idx = 10
        duplicate_row_xl_idx = 11
        assert excinfo.value.message == f'Subsample on row {duplicate_row_xl_idx} is a duplicate of subsample on row {duplicate_of_row_xl_idx}'


# class TestMetadataTypeErrors:
#     def test_with_missing_metadata_type(self, dataset_path):
#         # Modify bulk file

#         bulk_path = dataset_path / BULK_FILE_NAME

#         dfs = {
#             sheet_name: pd.read_excel(bulk_path, header=None, sheet_name=sheet_name)
#             for sheet_name in BULK_TEST_DATA
#         }

#         with pd.ExcelWriter(bulk_path) as writer:
#             for sheet_name, df in dfs.items():
#                 df.iloc[3, 2] = np.NaN
#                 df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
#                 break

#         # Build expected

#         expected_error_msg_kwargs = {
#             'workbook': BULK_FILE_NAME,
#             'worksheet': list(dfs)[0],
#             'cell': 'C4',
#         }

#         # Assert

#         with pytest.raises(IntegrityError) as excinfo:
#             with Dataset(dataset_path) as dataset:
#                 pass

#         assert excinfo.value.args[0] == ERROR_MESSAGES['metadata_type_missing'].format(**expected_error_msg_kwargs)




class TestResultTypes:
    def test_raises_with_blank_result_type(self, populated_dataset_path, bulk_wb_data):
        # Modify BULK

        bulk_ws_data = bulk_wb_data.worksheets[0]
        bulk_ws_data.result_type_metadata_sets[0] = \
            ('', bulk_ws_data.result_type_metadata_sets[0][1])
        bulk_wb_data.to_excel(populated_dataset_path / BULK_FILE_NAME)

        # Build expected

        # sample column (1) + subsample columns (n) + metadata type column (1)
        result_type_column_idx = 1 + len(bulk_ws_data.sample_subsample_results_sets[0][1]) + 1

        expected_error_values = {
            'workbook': BULK_FILE_NAME,
            'worksheet': bulk_wb_data.worksheets[0].name,
            'cell': xlref(0, result_type_column_idx),
            'message': ERROR_MESSAGES['missing_result_type']
        }

        # Assert

        with pytest.raises(IntegrityError) as excinfo:
            with Dataset(populated_dataset_path) as dataset:
                pass

        assert excinfo.value.workbook == expected_error_values['workbook']
        assert excinfo.value.worksheet == expected_error_values['worksheet']
        assert excinfo.value.cell == expected_error_values['cell']
        assert excinfo.value.message == expected_error_values['message']

    def test_with_NA_as_result_type(self, populated_dataset_path, bulk_wb_data):
        # Modify BULK

        for bulk_ws_data in bulk_wb_data.worksheets:
            bulk_ws_data.result_type_metadata_sets[0] = \
                ('NA', bulk_ws_data.result_type_metadata_sets[0][1])

        bulk_wb_data.to_excel(populated_dataset_path / BULK_FILE_NAME)

        # Assert

        with Dataset(populated_dataset_path) as dataset:
            assert set(dataset.bulk.results) == set(bulk_wb_data.expected_items)


class TestResults:
    def test(self, test_dataset_path, test_dataset_data):
        test_dataset_data.to_excel(test_dataset_path)

        with Dataset(test_dataset_path) as dataset:
            assert set(dataset.bulk.results) == set(test_dataset_data.workbooks['bulk'].expected_results)

    # Combinations of axes to test cleared

    AXES_TO_CLEAR = {
        '__'.join(sorted(axes)): axes
        for axes in list_of_subsets(('subsamples', 'metadata_types', 'result_types'))
    }

    @pytest.mark.parametrize('axes_to_clear', AXES_TO_CLEAR.values(), ids=AXES_TO_CLEAR.keys())
    def test_with_axes_cleared(self, test_dataset_path, test_dataset_data, axes_to_clear):
        for axis_to_clear in axes_to_clear:
            getattr(test_dataset_data.workbooks['bulk'], f"clear_{axis_to_clear}")()

        test_dataset_data.to_excel(test_dataset_path)

        with Dataset(test_dataset_path) as dataset:
            assert set(dataset.bulk.results) == set(test_dataset_data.workbooks['bulk'].expected_results)


class TestEmptyRegions:
    def test_raises_when_cells_right_of_subsamples_below_metadata_types_not_empty(self, test_dataset_path, test_dataset_data):
        mutations = {
            'BULK.xlsx': {
                'BULK1': {
                    'C9': 'Duchess'
                }
            }
        }

        test_dataset_data.to_excel(test_dataset_path, mutations)

        with pytest.raises(IntegrityError) as excinfo:
            with Dataset(test_dataset_path) as dataset:
                pass

        assert excinfo.value.workbook == 'BULK.xlsx'
        assert excinfo.value.worksheet == 'BULK1'
        assert excinfo.value.message == 'Metadata type in cell C9 cannot be given because a subsample exists on the same row'









# class TestSubsamples:
#     def test_raises_when_subsample_value_is_missing(self, dataset_path):
#         assert False

#         # Modify bulk file

#         bulk_path = dataset_path / BULK_FILE_NAME

#         dfs = {
#             sheet_name: pd.read_excel(bulk_path, header=None, sheet_name=sheet_name)
#             for sheet_name in BULK_TEST_DATA
#         }

#         with pd.ExcelWriter(bulk_path) as writer:
#             for sheet_name, df in dfs.items():
#                 df.iloc[8, 0] = np.NaN
#                 df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
#                 break

#         # Build expected

#         expected_error_msg_kwargs = {
#             'workbook': BULK_FILE_NAME,
#             'worksheet': list(dfs)[0],
#             'row': 9,
#         }

#         # Assert

#         with pytest.raises(IntegrityError) as excinfo:
#             with Dataset(dataset_path) as dataset:
#                 pass

#         assert excinfo.value.args[0] == ERROR_MESSAGES['subsample_values_missing'].format(**expected_error_msg_kwargs)

#     def test_raises_when_all_subsample_values_missing(self, dataset_path):
#         # Modify bulk file
#         assert False

#         bulk_path = dataset_path / BULK_FILE_NAME

#         dfs = {
#             sheet_name: pd.read_excel(bulk_path, header=None, sheet_name=sheet_name)
#             for sheet_name in BULK_TEST_DATA
#         }

#         with pd.ExcelWriter(bulk_path) as writer:
#             for sheet_name, df in dfs.items():
#                 df.iloc[9, 0] = np.NaN
#                 df.iloc[9, 1] = np.NaN
#                 df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
#                 break

#          # Build expected

#         expected_error_msg_kwargs = {
#             'workbook': BULK_FILE_NAME,
#             'worksheet': list(dfs)[0],
#             'row': 10,
#         }

#         # Assert

#         with pytest.raises(IntegrityError) as excinfo:
#             with Dataset(dataset_path) as dataset:
#                 pass

#         assert excinfo.value.args[0] == ERROR_MESSAGES['subsample_values_missing'].format(**expected_error_msg_kwargs)



#     def test_valid_with_trailing_whitespace_on_subsample(self, dataset_path):
#         bulk_wb_data = BulkWorkbookData.from_dict(BULK_TEST_DATA)

#         for bulk_ws_data in bulk_wb_data.worksheets.values():
#             bulk_ws_data.sample_subsample_results_sets = [
#                 (sample_idx, tuple(f'{x} \t' for x in subsample), results)
#                 for sample_idx, subsample, results in bulk_ws_data.sample_subsample_results_sets
#             ]

#         bulk_wb_data.to_excel(dataset_path / BULK_FILE_NAME)

#         with Dataset(dataset_path) as dataset:
#             assert set(dataset.bulk.results) == set(bulk_wb_data.expected_results)

#     def test_valid_with_deeper_subsample_levels(self, dataset_path):
#         bulk_wb_data = BulkWorkbookData.from_dict(BULK_TEST_DATA)

#         for bulk_ws_data in bulk_wb_data.worksheets.values():
#             bulk_ws_data.sample_subsample_results_sets = [
#                 (sample_idx, subsample + (subsample[-1] + '-deeper',), results)
#                 for sample_idx, subsample, results in bulk_ws_data.sample_subsample_results_sets
#             ]

#         bulk_wb_data.to_excel(dataset_path / BULK_FILE_NAME)

#         with Dataset(dataset_path) as dataset:
#             assert set(dataset.bulk.results) == set(bulk_wb_data.expected_results)






# class TestHeadings:
#     def test_missing_sample_heading(self, dataset_path):
#         # Modify bulk file

#         bulk_path = dataset_path / BULK_FILE_NAME

#         dfs = {
#             sheet_name: pd.read_excel(bulk_path, header=None, sheet_name=sheet_name)
#             for sheet_name in BULK_TEST_DATA
#         }

#         with pd.ExcelWriter(bulk_path) as writer:
#             for sheet_name, df in dfs.items():
#                 df.iloc[0, 0] = 'INVALID SAMPLES HEADING'
#                 df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
#                 break

#         # Build expected

#         expected_error_values = {
#             'workbook': BULK_FILE_NAME,
#             'worksheet': list(dfs)[0],
#             'cell': 'A1',
#             'message': ERROR_MESSAGES['sample_heading_missing']
#         }

#         # Assert

#         with pytest.raises(IntegrityError) as excinfo:
#             with Dataset(dataset_path) as dataset:
#                 pass

#         assert excinfo.value.workbook == expected_error_values['workbook']
#         assert excinfo.value.worksheet == expected_error_values['worksheet']
#         assert excinfo.value.cell == expected_error_values['cell']
#         assert excinfo.value.message == expected_error_values['message']

#     def test_missing_subsample_heading(self, dataset_path):
#         # Modify bulk file

#         bulk_path = dataset_path / BULK_FILE_NAME

#         dfs = {
#             sheet_name: pd.read_excel(bulk_path, header=None, sheet_name=sheet_name)
#             for sheet_name in BULK_TEST_DATA
#         }

#         with pd.ExcelWriter(bulk_path) as writer:
#             for sheet_name, df in dfs.items():
#                 df.iloc[0, 1] = 'INVALID SUBSAMPLE HEADING'
#                 df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
#                 break

#         # Build expected

#         expected_error_values = {
#             'workbook': BULK_FILE_NAME,
#             'worksheet': list(dfs)[0],
#             'cell': 'B1',
#             'message': ERROR_MESSAGES['subsample_heading_missing']
#         }

#         # Assert

#         with pytest.raises(IntegrityError) as excinfo:
#             with Dataset(dataset_path) as dataset:
#                 pass

#         assert excinfo.value.workbook == expected_error_values['workbook']
#         assert excinfo.value.worksheet == expected_error_values['worksheet']
#         assert excinfo.value.cell == expected_error_values['cell']
#         assert excinfo.value.message == expected_error_values['message']

#     def test_missing_metadata_type_heading(self, dataset_path):
#         # Modify bulk file

#         bulk_path = dataset_path / BULK_FILE_NAME

#         dfs = {
#             sheet_name: pd.read_excel(bulk_path, header=None, sheet_name=sheet_name)
#             for sheet_name in BULK_TEST_DATA
#         }

#         with pd.ExcelWriter(bulk_path) as writer:
#             for sheet_name, df in dfs.items():
#                 df.iloc[0, 2] = 'INVALID METADATA TYPE HEADING'
#                 df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
#                 break

#         # Build expected

#         expected_error_values = {
#             'workbook': BULK_FILE_NAME,
#             'worksheet': list(dfs)[0],
#             'cell': 'C1',
#             'message': ERROR_MESSAGES['metadata_type_heading_missing']
#         }

#         # Assert

#         with pytest.raises(IntegrityError) as excinfo:
#             with Dataset(dataset_path) as dataset:
#                 pass

#         assert excinfo.value.workbook == expected_error_values['workbook']
#         assert excinfo.value.worksheet == expected_error_values['worksheet']
#         assert excinfo.value.cell == expected_error_values['cell']
#         assert excinfo.value.message == expected_error_values['message']





# class TestDuplicateErrors:
#     def test_with_duplicate_result_type_metadata_set_in_same_worksheet(self, dataset_path):
#         # Modify bulk file

#         bulk_path = dataset_path / BULK_FILE_NAME

#         dfs = {
#             sheet_name: pd.read_excel(bulk_path, header=None, sheet_name=sheet_name)
#             for sheet_name in BULK_TEST_DATA
#         }

#         with pd.ExcelWriter(bulk_path) as writer:
#             for sheet_name, df in dfs.items():
#                 df[6] = df[5]
#                 df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
#                 break

#         # Build expected

#         expected_error_message_kwargs = {
#             'workbook': BULK_FILE_NAME,
#             'worksheet': list(dfs)[0],
#             'column': xlcolref(6),
#         }

#         # Assert

#         with pytest.raises(IntegrityError) as excinfo:
#             with Dataset(dataset_path) as dataset:
#                 pass

#         assert excinfo.value.args[0] == ERROR_MESSAGES['result_type_metadata_pair_duplicate'].format(**expected_error_message_kwargs)

#     def test_with_duplicate_subsample_result_type_metadata_set_in_different_worksheets(self, dataset_path):
#         # Modify bulk file

#         bulk_path = dataset_path / BULK_FILE_NAME

#         dfs = {
#             sheet_name: pd.read_excel(bulk_path, header=None, sheet_name=sheet_name)
#             for sheet_name in BULK_TEST_DATA
#         }

#         sheet_names = list(dfs.keys())
#         dfs[sheet_names[1]] = dfs[sheet_names[0]]

#         with pd.ExcelWriter(bulk_path) as writer:
#             for sheet_name, df in dfs.items():
#                 df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)

#         # Build expected

#         expected_error_message_kwargs = {
#             'workbook': BULK_FILE_NAME,
#             'worksheet': list(dfs)[0],
#             'column': xlcolref(6),
#         }

#         with pytest.raises(IntegrityError) as excinfo:
#             with Dataset(dataset_path) as dataset:
#                 pass


#         assert excinfo.value.args[0] == ERROR_MESSAGES['subsample_result_type_metadata_pair_duplicate'].format(**expected_error_message_kwargs)

#     def test_with_duplicate_metadata_type_in_same_worksheet(self, dataset_path):
#         # Modify bulk file

#         bulk_path = dataset_path / BULK_FILE_NAME

#         dfs = {
#             sheet_name: pd.read_excel(bulk_path, header=None, sheet_name=sheet_name)
#             for sheet_name in BULK_TEST_DATA
#         }

#         with pd.ExcelWriter(bulk_path) as writer:
#             for sheet_name, df in dfs.items():
#                 df.iloc[4, 2] = df.iloc[3, 2]
#                 df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
#                 break

#         # Build expected

#         expected_error_msg_kwargs = {
#             'workbook': BULK_FILE_NAME,
#             'worksheet': list(dfs)[0],
#             'cell': 'C5',
#         }

#         # Assert

#         with pytest.raises(IntegrityError) as excinfo:
#             with Dataset(dataset_path) as dataset:
#                 pass

#         assert excinfo.value.args[0] == ERROR_MESSAGES['metadata_type_duplicate'].format(**expected_error_msg_kwargs)
