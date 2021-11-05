import pytest

from geochem_dataset_excel import Dataset
from geochem_dataset_excel.exceptions import InvalidDatasetNameError


class TestDataset:
    def test_dataset(self, tmp_path):
        dataset_path = tmp_path / 'ca.cngo.test'
        dataset_path.mkdir()

        dataset = Dataset(dataset_path)

        assert isinstance(dataset, Dataset)
        assert dataset.path == dataset_path
        assert dataset.name == dataset_path.name

    def test_dataset_with_non_existant_path(self, tmp_path):
        dataset_path = tmp_path / 'ca.cngo.test'

        with pytest.raises(NotADirectoryError):
            Dataset(dataset_path)

    def test_dataset_with_file_path(self, tmp_path):
        dataset_path = tmp_path / 'ca.cngo.test'
        dataset_path.touch()

        with pytest.raises(NotADirectoryError):
            Dataset(dataset_path)

    def test_dataset_with_invalid_name(self, tmp_path):
        dataset_path = tmp_path / 'skittles'
        dataset_path.mkdir()

        with pytest.raises(InvalidDatasetNameError) as excinfo:
            dataset = Dataset(dataset_path)

        assert excinfo.value.args[0] == 'Dataset name must use reverse domain name notation'
