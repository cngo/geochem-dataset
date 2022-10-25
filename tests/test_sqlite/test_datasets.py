from geochem_dataset.sqlite.models import Dataset
import pytest

from tests.helpers.utils import DeleteField, kwargs_without_id, modified_kwargs
from .sample_data import DATASET_COLUMNS, DATASETS

DELETE_ID_FIELD = ('id', DeleteField)


class TestCreate:
    VALID_FIELD_DATA = {
        'id__not_given': [DELETE_ID_FIELD],
        'id__NoneType':  [('id', None)],

        'extra__not_given': [DELETE_ID_FIELD, ('extra', DeleteField)],
        'extra__NoneType':  [DELETE_ID_FIELD, ('extra', None)],
    }

    @pytest.mark.parametrize('modifications', VALID_FIELD_DATA.values(), ids=VALID_FIELD_DATA.keys())
    def test_valid(self, initialized_db, modifications):
        kwargs = dict(zip(DATASET_COLUMNS, DATASETS[0]))
        mod_kwargs = modified_kwargs(kwargs, modifications)

        dataset = initialized_db.datasets.create(**mod_kwargs)

        assert dataset.id == kwargs['id']
        assert dataset.name == mod_kwargs['name']
        assert dataset.extra == mod_kwargs.get('extra', None)

    INVALID_FIELD_DATA = {
        'id__wrong_type__str': ([('id', 'Skittles')], TypeError),

        'name__not_given':                 ([DELETE_ID_FIELD, ('name', DeleteField)], TypeError),
        'name__wrong_type__NoneType':      ([DELETE_ID_FIELD, ('name', None)], TypeError),
        'name__wrong_type__int':           ([DELETE_ID_FIELD, ('name', 99)], TypeError),
        'name__wrong_value__empty_string': ([DELETE_ID_FIELD, ('name', '')], ValueError),
        'name__wrong_pattern':             ([DELETE_ID_FIELD, ('name', 'test')], ValueError),

        'extra__wrong_type__str':            ([DELETE_ID_FIELD, ('extra', 'Skittles')], TypeError),
        'extra__wrong_type__int':            ([DELETE_ID_FIELD, ('extra', 99)], TypeError),
        'extra__wrong_item_key_type__int':   ([DELETE_ID_FIELD, ('extra', {844: 'Skittles', 'two_cat': 'Duchess'})], TypeError),
        'extra__wrong_item_value_type__int': ([DELETE_ID_FIELD, ('extra', {'one_cat': 844, 'two_cat': 'Duchess'})],  TypeError),
    }

    @pytest.mark.parametrize('modifications, expected_exc', INVALID_FIELD_DATA.values(), ids=INVALID_FIELD_DATA.keys())
    def test_invalid(self, initialized_db, modifications, expected_exc):
        kwargs = dict(zip(DATASET_COLUMNS, DATASETS[0]))
        mod_kwargs = modified_kwargs(kwargs, modifications)

        with pytest.raises(expected_exc):
            initialized_db.datasets.create(**mod_kwargs)

    def test_with_duplicate_name(self, populated_db):
        kwargs = dict(zip(DATASET_COLUMNS, DATASETS[0]))
        mod_kwargs = kwargs_without_id(kwargs)

        with pytest.raises(ValueError):
            populated_db.datasets.create(**mod_kwargs)


class TestGetByID:
    @pytest.mark.parametrize('kwargs', [dict(zip(DATASET_COLUMNS, x)) for x in DATASETS])
    def test_valid(self, populated_db, kwargs):
        dataset = populated_db.datasets.get_by_id(kwargs['id'])

        assert dataset.id == kwargs['id']
        assert dataset.name == kwargs['name']
        assert dataset.extra == kwargs['extra']

    INVALID_ID_DATA = {
        'wrong_type__str':      ('Skittles',),
        'wrong_type__NoneType': (None,),
        'wrong_type__dict':     ({'cat': 'Skittles'},),
    }

    @pytest.mark.parametrize('id', list(INVALID_ID_DATA.values()), ids=list(INVALID_ID_DATA.keys()))
    def test_invalid(self, initialized_db, id):
        with pytest.raises(TypeError) as excinfo:
            initialized_db.datasets.get_by_id(id)

    def test_non_existant(self, initialized_db):
        dataset = initialized_db.datasets.get_by_id(99)
        assert dataset is None


class TestGetByName:
    @pytest.mark.parametrize('kwargs', [dict(zip(DATASET_COLUMNS, x)) for x in DATASETS])
    def test_valid(self, populated_db, kwargs):
        dataset = populated_db.datasets.get_by_name(kwargs['name'])

        assert dataset.id == kwargs['id']
        assert dataset.name == kwargs['name']
        assert dataset.extra == kwargs['extra']

    INVALID_NAME_DATA = {
        'wrong_type__int':      (8,),
        'wrong_type__NoneType': (None,),
        'wrong_type__dict':     ({'cat': 'Skittles'},),
    }

    @pytest.mark.parametrize('name', list(INVALID_NAME_DATA.values()), ids=list(INVALID_NAME_DATA.keys()))
    def test_invalid(self, initialized_db, name):
        with pytest.raises(TypeError) as excinfo:
            initialized_db.datasets.get_by_name(name)

    def test_non_existant(self, initialized_db):
        dataset = initialized_db.datasets.get_by_name('ca.cngo.test')
        assert dataset is None


class TestIter:
    def test_with_initialized_db(self, initialized_db):
        datasets = list(initialized_db.datasets)

        expected_datasets = list()
        assert datasets == expected_datasets

    def test_with_populated_db(self, populated_db):
        datasets = list(populated_db.datasets)

        for idx, dataset in enumerate(datasets):
            kwargs = dict(zip(DATASET_COLUMNS, DATASETS[idx]))

            assert dataset.id == kwargs['id']
            assert dataset.name == kwargs['name']
            assert dataset.extra == kwargs['extra']
