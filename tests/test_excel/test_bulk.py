import copy
import itertools
import re
from typing import Iterable

import pytest

from geochem_dataset.excel import Dataset
from geochem_dataset.excel.exceptions import IntegrityError

from .conftest import ERROR_MESSAGES, ANALYSIS_WORKBOOK_ERROR_MESSAGES
from ..helpers.utils import xlrowref


"""
Structure of BULK worksheet:

| SAMPLE   | SUBSAMPLE     | METADATA_TYPE   | result_type_1 | ... | result_type_m | ████
| ████████ | █████████████ | metadata_type_1 | metadata_1.1  | ... | metadata_m.1  | ████
| ████████ | █████████████ | ...             | ...           | ... | ...           | ████
| ████████ | █████████████ | metadata_type_n | metadata_1.n  | ... | metadata_m.n  | ████
| sample_1 | subsample_1.1 | ███████████████ | result_1,1.1  | ... | result_m,1.1  | ████
| ...      | ...           | ███████████████ | ...           | ... | ...           | ████
| sample_1 | subsample_1.A | ███████████████ | result_1,1.A  | ... | result_m,1.A  | ████
| ...      | ...           | ███████████████ | ...           | ... | ...           | ████
| sample_a | subsample_a.1 | ███████████████ | result_1,a.1  | ... | result_m,a.1  | ████
| ...      | ...           | ███████████████ | ...           | ... | ...           | ████
| sample_a | subsample_a.B | ███████████████ | result_1,a.B  | ... | result_m,a.B  | ████
| ████████ | █████████████ | ███████████████ | ████████████  | ███ | █████████████ | ████

█ = Empty cell
"""


def test_raises_when_bulk_is_accessed_without_workbook(fixture_dataset_excel):
    dataset_path, dataset_excel_data = fixture_dataset_excel
    dataset_excel_data.to_excel(dataset_path)

    bulk_path = dataset_path / 'BULK.xlsx'
    bulk_path.unlink()

    with Dataset(dataset_path) as dataset:
        with pytest.raises(AttributeError):
            dataset.bulk



# SUBAMPLE TESTS:
# non-existent sample value
# empty sample value
# empty subsample value
# empty subsubsample value (TODO)
# invalid subsample value (TODO)
# invalid subsubsample value (TODO)
# duplicate subsample in same worksheet
# duplicate subsubsample in same worksheet (TODO)
# duplicate subsample in different worksheet (TODO)
# duplicate subsubsample in different worksheet (TODO)

# METADATA TYPE TESTS:
# empty metadata type value
# invalid metadata type value (TODO)

# RESULT TYPE TESTS:
# empty result type value


class TestBulkSubsampleErrors:
    def test_raises_with_non_existant_sample_value(self, fixture_dataset_excel):
        dataset_path, dataset_excel_data = fixture_dataset_excel

        dataset_excel_data['BULK.xlsx']['BULK1'].data['subsample_results_sets'][0][0][0] = 'Duchess'
        dataset_excel_data.to_excel(dataset_path)

        expected_error_match = re.escape(ERROR_MESSAGES['fk_constraint_violation__columns'].format(
            columns     = 'SAMPLE',
            row         = 9,
            value       = 'Duchess',
            fk_workbook = 'SAMPLES.xlsx'
        ))

        with pytest.raises(IntegrityError, match=expected_error_match) as excinfo:
            with Dataset(dataset_path) as _:
                pass

        assert excinfo.value.workbook == 'BULK.xlsx'
        assert excinfo.value.worksheet == 'BULK1'

    def test_raises_with_empty_sample_value(self, fixture_dataset_excel):
        dataset_path, dataset_excel_data = fixture_dataset_excel

        dataset_excel_data['BULK.xlsx']['BULK1'].data['subsample_results_sets'][0][0][0] = ''
        dataset_excel_data.to_excel(dataset_path)

        expected_error_match = re.escape(ERROR_MESSAGES['empty_value__column'].format(
            column = 'SAMPLE',
            row    = 9,
        ))

        with pytest.raises(IntegrityError, match=expected_error_match) as excinfo:
            with Dataset(dataset_path) as _:
                pass

        assert excinfo.value.workbook == 'BULK.xlsx'
        assert excinfo.value.worksheet == 'BULK1'

    def test_raises_with_empty_subsample_value(self, fixture_dataset_excel):
        dataset_path, dataset_excel_data = fixture_dataset_excel

        dataset_excel_data['BULK.xlsx']['BULK1'].data['subsample_results_sets'][0][0][1] = ''
        dataset_excel_data.to_excel(dataset_path)

        expected_error_match = re.escape(ERROR_MESSAGES['empty_value__column'].format(
            column = 'SUBSAMPLE',
            row    = 9,
        ))

        with pytest.raises(IntegrityError, match=expected_error_match) as excinfo:
            with Dataset(dataset_path) as _:
                pass

        assert excinfo.value.workbook == 'BULK.xlsx'
        assert excinfo.value.worksheet == 'BULK1'

    def test_raises_with_empty_subsubsample_value(self, fixture_dataset_excel):  # TODO
        raise NotImplementedError()

    def test_raises_with_invalid_subsample_value(self, fixture_dataset_excel):  # TODO
        raise NotImplementedError()

    def test_raises_with_invalid_subsubsample_value(self, fixture_dataset_excel):  # TODO
        raise NotImplementedError()

    def test_raises_with_duplicate_subsmaple_in_same_worksheet(self, fixture_dataset_excel):
        dataset_path, dataset_excel_data = fixture_dataset_excel

        existing_subsample_row = dataset_excel_data.workbooks['BULK.xlsx'].worksheets['BULK1'].data['subsample_results_sets'][-1]
        dataset_excel_data.workbooks['BULK.xlsx'].worksheets['BULK1'].data['subsample_results_sets'].append(existing_subsample_row)
        dataset_excel_data.to_excel(dataset_path)

        expected_error_match = re.escape(ERROR_MESSAGES['unique_constraint_violation__columns'].format(
            columns          = 'SAMPLE, SUBSAMPLE',
            row              = 11,
            value            = 'Duchess',
            duplicate_of_row = 10
        ))

        with pytest.raises(IntegrityError, match=expected_error_match) as excinfo:
            with Dataset(dataset_path) as _:
                pass

        assert excinfo.value.workbook == 'BULK.xlsx'
        assert excinfo.value.worksheet == 'BULK1'

    def test_raises_with_duplicate_subsubsample_in_same_worksheet(self, fixture_dataset_excel):  # TODO
        raise NotImplementedError()

    def test_raises_with_duplicate_subsample_in_different_worksheet(self, fixture_dataset_excel):  # TODO
        raise NotImplementedError()

    def test_raises_with_duplicate_subsubsample_in_different_worksheet(self, fixture_dataset_excel):  # TODO
        raise NotImplementedError()


class TestBulkMetadataTypeErrors:
    def test_raises_with_empty_metadata_type_value(self, fixture_dataset_excel):
        dataset_path, dataset_excel_data = fixture_dataset_excel

        dataset_excel_data['BULK.xlsx']['BULK1'].data['metadata_types'][0] = ''
        dataset_excel_data.to_excel(dataset_path)

        expected_error_match = re.escape(ERROR_MESSAGES['empty_value__column'].format(
            column = 'METADATA_TYPE',
            row    = 2,
        ))

        with pytest.raises(IntegrityError, match=expected_error_match) as excinfo:
            with Dataset(dataset_path) as _:
                pass

        assert excinfo.value.workbook == 'BULK.xlsx'
        assert excinfo.value.worksheet == 'BULK1'

    def test_raises_with_invalid_metadata_type_value(self, fixture_dataset_excel):
        raise NotImplementedError()


class TestBulkResultType:
    def test(self, fixture_dataset_excel):
        dataset_path, dataset_excel_data = fixture_dataset_excel
        dataset_excel_data.to_excel(dataset_path)

        expected_bulk_data = dataset_excel_data.workbooks['BULK.xlsx']
        expected_results = list(expected_bulk_data.iter_objects())

        with Dataset(dataset_path) as dataset:
            results = list(dataset.bulk.results)
            assert results == expected_results

    def test_with_NA_result_type_value(self, fixture_dataset_excel):
        dataset_path, dataset_excel_data = fixture_dataset_excel

        dataset_excel_data['BULK.xlsx']['BULK1'].data['result_type_metadata_sets'][0][0] = 'NA'
        dataset_excel_data.to_excel(dataset_path)

        expected_bulk_data = dataset_excel_data.workbooks['BULK.xlsx']
        expected_results = list(expected_bulk_data.iter_objects())

        with Dataset(dataset_path) as dataset:
            results = list(dataset.bulk.results)
            assert results == expected_results


class TestBulkResultTypeErrors:
    def test_raises_with_empty_result_type_value(self, fixture_dataset_excel):
        dataset_path, dataset_excel_data = fixture_dataset_excel

        dataset_excel_data['BULK.xlsx']['BULK1'].data['result_type_metadata_sets'][0][0] = ''
        dataset_excel_data.to_excel(dataset_path)

        expected_error_match = re.escape(ERROR_MESSAGES['result_type__missing'].format(
            cell = 'D1'
        ))

        with pytest.raises(IntegrityError, match=expected_error_match) as excinfo:
            with Dataset(dataset_path) as _:
                pass

        assert excinfo.value.workbook == 'BULK.xlsx'
        assert excinfo.value.worksheet == 'BULK1'


def list_of_subsets(items: Iterable) -> list:
    """Return all combinations of subsets of given set of items. Different sizes of subsets will be
    returned, starting with just one item and ending with all items."""

    return list(itertools.chain(*list(itertools.combinations(items, r) for r in range(1, len(items) + 1))))


class Test:
    AXES_TO_CLEAR = {
        '__'.join(sorted(axes)): axes
        for axes in list_of_subsets(('subsamples', 'metadata_types', 'result_types'))
    }

    @pytest.mark.parametrize('axes_to_clear', AXES_TO_CLEAR.values(), ids=AXES_TO_CLEAR.keys())
    def test_with_axes_cleared(self, fixture_dataset_excel, axes_to_clear):
        dataset_path, dataset_excel_data = fixture_dataset_excel

        for ws_data in dataset_excel_data.workbooks['BULK.xlsx'].worksheets.values():
            for axis_to_clear in axes_to_clear:
                clear_fn_name = f'clear_{axis_to_clear}'
                clear_fn = getattr(ws_data, clear_fn_name)
                clear_fn()

        dataset_excel_data.to_excel(dataset_path)

        expected_bulk_data = dataset_excel_data.workbooks['BULK.xlsx']
        expected_results = list(expected_bulk_data.iter_objects())

        with Dataset(dataset_path) as dataset:
            results = list(dataset.bulk.results)
            assert results == expected_results





class TestEmptyRegionErrors:
    # def test_raises_when_cells_below_subsample_headings_not_empty(self, fixture_dataset_excel):
    #     dataset_path, dataset_excel_data = fixture_dataset_excel

    #     mods = {'BULK.xlsx': {'BULK1': {
    #         'A2': '11TIAT001A01', 'B2': 'Skittles1',
    #         'A3': '11TIAT001A01', 'B3': 'Skittles2',
    #         'A4': '11TIAT001A01', 'B4': 'Skittles3',
    #         'A5': '11TIAT001A01', 'B5': 'Skittles4',
    #         'A6': '11TIAT001A01', 'B6': 'Skittles5',
    #         'A7': '11TIAT001A01', 'B7': 'Skittles6',
    #         'A8': '11TIAT001A01', 'B8': 'Skittles7',
    #     }}}
    #     dataset_excel_data.to_excel(dataset_path, mods)

    #     expected_error_match = re.escape(ERROR_MESSAGES['cell_not_empty'].format(
    #         cell   = 'A2',
    #         reason = 'a metadata type exists on the same row',
    #     ))

    #     with pytest.raises(IntegrityError, match=expected_error_match) as excinfo:
    #         with Dataset(dataset_path) as _:
    #             pass

    #     assert excinfo.value.workbook == 'BULK.xlsx'
    #     assert excinfo.value.worksheet == 'BULK1'

    def test_raises_when_cells_below_metadata_types_not_empty(self, fixture_dataset_excel):
        dataset_path, dataset_excel_data = fixture_dataset_excel

        mods = {'BULK.xlsx': {'BULK1': {'C9': 'Duchess'}}}
        dataset_excel_data.to_excel(dataset_path, mods)

        expected_error_match = re.escape(ERROR_MESSAGES['cell_not_empty'].format(
            cell   = 'C9',
            reason = 'a subsample exists on the same row',
        ))

        with pytest.raises(IntegrityError, match=expected_error_match) as excinfo:
            with Dataset(dataset_path) as _:
                pass

        assert excinfo.value.workbook == 'BULK.xlsx'
        assert excinfo.value.worksheet == 'BULK1'









# # class TestSubsamples:
# #     def test_raises_when_subsample_value_is_missing(self, dataset_path):
# #         assert False

# #         # Modify bulk file

# #         bulk_path = dataset_path / 'BULK.xlsx'

# #         dfs = {
# #             sheet_name: pd.read_excel(bulk_path, header=None, sheet_name=sheet_name)
# #             for sheet_name in BULK_TEST_DATA
# #         }

# #         with pd.ExcelWriter(bulk_path) as writer:
# #             for sheet_name, df in dfs.items():
# #                 df.iloc[8, 0] = np.NaN
# #                 df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
# #                 break

# #         # Build expected

# #         expected_error_msg_kwargs = {
# #             'workbook': 'BULK.xlsx',
# #             'worksheet': list(dfs)[0],
# #             'row': 9,
# #         }

# #         # Assert

# #         with pytest.raises(IntegrityError) as excinfo:
# #             with Dataset(dataset_path) as dataset:
# #                 pass

# #         assert excinfo.value.args[0] == ERROR_MESSAGES['subsample_values_missing'].format(**expected_error_msg_kwargs)

# #     def test_raises_when_all_subsample_values_missing(self, dataset_path):
# #         # Modify bulk file
# #         assert False

# #         bulk_path = dataset_path / 'BULK.xlsx'

# #         dfs = {
# #             sheet_name: pd.read_excel(bulk_path, header=None, sheet_name=sheet_name)
# #             for sheet_name in BULK_TEST_DATA
# #         }

# #         with pd.ExcelWriter(bulk_path) as writer:
# #             for sheet_name, df in dfs.items():
# #                 df.iloc[9, 0] = np.NaN
# #                 df.iloc[9, 1] = np.NaN
# #                 df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
# #                 break

# #          # Build expected

# #         expected_error_msg_kwargs = {
# #             'workbook': 'BULK.xlsx',
# #             'worksheet': list(dfs)[0],
# #             'row': 10,
# #         }

# #         # Assert

# #         with pytest.raises(IntegrityError) as excinfo:
# #             with Dataset(dataset_path) as dataset:
# #                 pass

# #         assert excinfo.value.args[0] == ERROR_MESSAGES['subsample_values_missing'].format(**expected_error_msg_kwargs)



# #     def test_valid_with_trailing_whitespace_on_subsample(self, dataset_path):
# #         bulk_wb_data = BulkWorkbookData.from_dict(BULK_TEST_DATA)

# #         for bulk_ws_data in bulk_wb_data.worksheets.values():
# #             bulk_ws_data.sample_subsample_results_sets = [
# #                 (sample_idx, tuple(f'{x} \t' for x in subsample), results)
# #                 for sample_idx, subsample, results in bulk_ws_data.sample_subsample_results_sets
# #             ]

# #         bulk_wb_data.to_excel(dataset_path / 'BULK.xlsx')

# #         with Dataset(dataset_path) as dataset:
# #             assert set(dataset.bulk.results) == set(bulk_wb_data.expected_results)

# #     def test_valid_with_deeper_subsample_levels(self, dataset_path):
# #         bulk_wb_data = BulkWorkbookData.from_dict(BULK_TEST_DATA)

# #         for bulk_ws_data in bulk_wb_data.worksheets.values():
# #             bulk_ws_data.sample_subsample_results_sets = [
# #                 (sample_idx, subsample + (subsample[-1] + '-deeper',), results)
# #                 for sample_idx, subsample, results in bulk_ws_data.sample_subsample_results_sets
# #             ]

# #         bulk_wb_data.to_excel(dataset_path / 'BULK.xlsx')

# #         with Dataset(dataset_path) as dataset:
# #             assert set(dataset.bulk.results) == set(bulk_wb_data.expected_results)






# # class TestHeadings:
# #     def test_missing_sample_heading(self, dataset_path):
# #         # Modify bulk file

# #         bulk_path = dataset_path / 'BULK.xlsx'

# #         dfs = {
# #             sheet_name: pd.read_excel(bulk_path, header=None, sheet_name=sheet_name)
# #             for sheet_name in BULK_TEST_DATA
# #         }

# #         with pd.ExcelWriter(bulk_path) as writer:
# #             for sheet_name, df in dfs.items():
# #                 df.iloc[0, 0] = 'INVALID SAMPLES HEADING'
# #                 df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
# #                 break

# #         # Build expected

# #         expected_error_values = {
# #             'workbook': 'BULK.xlsx',
# #             'worksheet': list(dfs)[0],
# #             'cell': 'A1',
# #             'message': ERROR_MESSAGES['sample_heading_missing']
# #         }

# #         # Assert

# #         with pytest.raises(IntegrityError) as excinfo:
# #             with Dataset(dataset_path) as dataset:
# #                 pass

# #         assert excinfo.value.workbook == expected_error_values['workbook']
# #         assert excinfo.value.worksheet == expected_error_values['worksheet']
# #         assert excinfo.value.cell == expected_error_values['cell']
# #         assert excinfo.value.message == expected_error_values['message']

# #     def test_missing_subsample_heading(self, dataset_path):
# #         # Modify bulk file

# #         bulk_path = dataset_path / 'BULK.xlsx'

# #         dfs = {
# #             sheet_name: pd.read_excel(bulk_path, header=None, sheet_name=sheet_name)
# #             for sheet_name in BULK_TEST_DATA
# #         }

# #         with pd.ExcelWriter(bulk_path) as writer:
# #             for sheet_name, df in dfs.items():
# #                 df.iloc[0, 1] = 'INVALID SUBSAMPLE HEADING'
# #                 df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
# #                 break

# #         # Build expected

# #         expected_error_values = {
# #             'workbook': 'BULK.xlsx',
# #             'worksheet': list(dfs)[0],
# #             'cell': 'B1',
# #             'message': ERROR_MESSAGES['subsample_heading_missing']
# #         }

# #         # Assert

# #         with pytest.raises(IntegrityError) as excinfo:
# #             with Dataset(dataset_path) as dataset:
# #                 pass

# #         assert excinfo.value.workbook == expected_error_values['workbook']
# #         assert excinfo.value.worksheet == expected_error_values['worksheet']
# #         assert excinfo.value.cell == expected_error_values['cell']
# #         assert excinfo.value.message == expected_error_values['message']

# #     def test_missing_metadata_type_heading(self, dataset_path):
# #         # Modify bulk file

# #         bulk_path = dataset_path / 'BULK.xlsx'

# #         dfs = {
# #             sheet_name: pd.read_excel(bulk_path, header=None, sheet_name=sheet_name)
# #             for sheet_name in BULK_TEST_DATA
# #         }

# #         with pd.ExcelWriter(bulk_path) as writer:
# #             for sheet_name, df in dfs.items():
# #                 df.iloc[0, 2] = 'INVALID METADATA TYPE HEADING'
# #                 df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
# #                 break

# #         # Build expected

# #         expected_error_values = {
# #             'workbook': 'BULK.xlsx',
# #             'worksheet': list(dfs)[0],
# #             'cell': 'C1',
# #             'message': ERROR_MESSAGES['metadata_type_heading_missing']
# #         }

# #         # Assert

# #         with pytest.raises(IntegrityError) as excinfo:
# #             with Dataset(dataset_path) as dataset:
# #                 pass

# #         assert excinfo.value.workbook == expected_error_values['workbook']
# #         assert excinfo.value.worksheet == expected_error_values['worksheet']
# #         assert excinfo.value.cell == expected_error_values['cell']
# #         assert excinfo.value.message == expected_error_values['message']





# # class TestDuplicateErrors:
# #     def test_with_duplicate_result_type_metadata_set_in_same_worksheet(self, dataset_path):
# #         # Modify bulk file

# #         bulk_path = dataset_path / 'BULK.xlsx'

# #         dfs = {
# #             sheet_name: pd.read_excel(bulk_path, header=None, sheet_name=sheet_name)
# #             for sheet_name in BULK_TEST_DATA
# #         }

# #         with pd.ExcelWriter(bulk_path) as writer:
# #             for sheet_name, df in dfs.items():
# #                 df[6] = df[5]
# #                 df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
# #                 break

# #         # Build expected

# #         expected_error_message_kwargs = {
# #             'workbook': 'BULK.xlsx',
# #             'worksheet': list(dfs)[0],
# #             'column': xlcolref(6),
# #         }

# #         # Assert

# #         with pytest.raises(IntegrityError) as excinfo:
# #             with Dataset(dataset_path) as dataset:
# #                 pass

# #         assert excinfo.value.args[0] == ERROR_MESSAGES['result_type_metadata_pair_duplicate'].format(**expected_error_message_kwargs)

# #     def test_with_duplicate_subsample_result_type_metadata_set_in_different_worksheets(self, dataset_path):
# #         # Modify bulk file

# #         bulk_path = dataset_path / 'BULK.xlsx'

# #         dfs = {
# #             sheet_name: pd.read_excel(bulk_path, header=None, sheet_name=sheet_name)
# #             for sheet_name in BULK_TEST_DATA
# #         }

# #         sheet_names = list(dfs.keys())
# #         dfs[sheet_names[1]] = dfs[sheet_names[0]]

# #         with pd.ExcelWriter(bulk_path) as writer:
# #             for sheet_name, df in dfs.items():
# #                 df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)

# #         # Build expected

# #         expected_error_message_kwargs = {
# #             'workbook': 'BULK.xlsx',
# #             'worksheet': list(dfs)[0],
# #             'column': xlcolref(6),
# #         }

# #         with pytest.raises(IntegrityError) as excinfo:
# #             with Dataset(dataset_path) as dataset:
# #                 pass


# #         assert excinfo.value.args[0] == ERROR_MESSAGES['subsample_result_type_metadata_pair_duplicate'].format(**expected_error_message_kwargs)

# #     def test_with_duplicate_metadata_type_in_same_worksheet(self, dataset_path):
# #         # Modify bulk file

# #         bulk_path = dataset_path / 'BULK.xlsx'

# #         dfs = {
# #             sheet_name: pd.read_excel(bulk_path, header=None, sheet_name=sheet_name)
# #             for sheet_name in BULK_TEST_DATA
# #         }

# #         with pd.ExcelWriter(bulk_path) as writer:
# #             for sheet_name, df in dfs.items():
# #                 df.iloc[4, 2] = df.iloc[3, 2]
# #                 df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
# #                 break

# #         # Build expected

# #         expected_error_msg_kwargs = {
# #             'workbook': 'BULK.xlsx',
# #             'worksheet': list(dfs)[0],
# #             'cell': 'C5',
# #         }

# #         # Assert

# #         with pytest.raises(IntegrityError) as excinfo:
# #             with Dataset(dataset_path) as dataset:
# #                 pass

# #         assert excinfo.value.args[0] == ERROR_MESSAGES['metadata_type_duplicate'].format(**expected_error_msg_kwargs)
