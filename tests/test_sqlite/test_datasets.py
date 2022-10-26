from geochem_dataset.sqlite.models import Dataset
import pytest

from tests.helpers.utils import (
    DICT_MOD_SET, DICT_MOD_DELETE,
    DictMod, set_mods, set_none_mods, delete_mods,
    modified_dict, dict_without
)

from .sample_data import DATASET_COLUMNS, DATASETS

class TestCreate:
    VALID_FIELD_DATA = {
        'id__not_given': delete_mods('id'),
        'id__NoneType':  set_none_mods('id'),

        'extra__not_given': delete_mods('id', 'extra'),
        'extra__NoneType':  delete_mods('id') + set_none_mods('extra'),
    }

    @pytest.mark.parametrize('modifications', VALID_FIELD_DATA.values(), ids=VALID_FIELD_DATA.keys())
    def test_valid(self, empty_db, modifications):
        db = empty_db

        kwargs = dict(zip(DATASET_COLUMNS, DATASETS[0]))
        mod_kwargs = modified_dict(kwargs, modifications)

        dataset = db.datasets.create(**mod_kwargs)

        assert dataset.id == kwargs['id']
        assert dataset.name == mod_kwargs['name']
        assert dataset.extra == mod_kwargs.get('extra', None)

    INVALID_FIELD_DATA = {
        'id__wrong_type__str': (set_mods('id', value='Skittles'), TypeError),

        'name__not_given':                 (delete_mods('id', 'name'), TypeError),
        'name__wrong_type__NoneType':      (delete_mods('id') + set_none_mods('name'), TypeError),
        'name__wrong_type__int':           (delete_mods('id') + set_mods('name', value=99), TypeError),
        'name__wrong_value__empty_string': (delete_mods('id') + set_mods('name', value=''), ValueError),
        'name__wrong_pattern':             (delete_mods('id') + set_mods('name', value='test'), ValueError),

        'extra__wrong_type__str':            (delete_mods('id') + set_mods('extra', value='Skittles'), TypeError),
        'extra__wrong_type__int':            (delete_mods('id') + set_mods('extra', value=99), TypeError),
        'extra__wrong_item_key_type__int':   (delete_mods('id') + set_mods('extra', value={844: 'Skittles', 'two_cat': 'Duchess'}), TypeError),
        'extra__wrong_item_value_type__int': (delete_mods('id') + set_mods('extra', value={'one_cat': 844, 'two_cat': 'Duchess'}),  TypeError),
    }

    @pytest.mark.parametrize('modifications, expected_exc', INVALID_FIELD_DATA.values(), ids=INVALID_FIELD_DATA.keys())
    def test_invalid(self, empty_db, modifications, expected_exc):
        db = empty_db

        kwargs = dict(zip(DATASET_COLUMNS, DATASETS[0]))
        mod_kwargs = modified_dict(kwargs, modifications)

        with pytest.raises(expected_exc):
            db.datasets.create(**mod_kwargs)

    def test_with_duplicate_name(self, populated_db):
        kwargs = dict(zip(DATASET_COLUMNS, DATASETS[0]))
        mod_kwargs = dict_without(kwargs, 'id')

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
    def test_invalid(self, empty_db, id):
        db = empty_db

        with pytest.raises(TypeError) as excinfo:
            db.datasets.get_by_id(id)

    def test_non_existant(self, empty_db):
        db = empty_db

        dataset = db.datasets.get_by_id(99)
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
    def test_invalid(self, empty_db, name):
        db = empty_db

        with pytest.raises(TypeError) as excinfo:
            db.datasets.get_by_name(name)

    def test_non_existant(self, empty_db):
        db = empty_db

        dataset = db.datasets.get_by_name('ca.cngo.test')
        assert dataset is None


class TestIter:
    def test_with_empty_db(self, empty_db):
        db = empty_db

        datasets = list(db.datasets)

        expected_datasets = list()
        assert datasets == expected_datasets

    def test_with_populated_db(self, populated_db):
        datasets = list(populated_db.datasets)

        for idx, dataset in enumerate(datasets):
            kwargs = dict(zip(DATASET_COLUMNS, DATASETS[idx]))

            assert dataset.id == kwargs['id']
            assert dataset.name == kwargs['name']
            assert dataset.extra == kwargs['extra']
