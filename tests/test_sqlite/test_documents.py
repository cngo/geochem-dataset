from geochem_dataset.sqlite.models import Dataset
import pytest

from tests.helpers.utils import (
    DICT_MOD_SET, DICT_MOD_DELETE,
    DictMod, set_mod, set_mods, set_none_mods, delete_mod, delete_mods,
    modified_dict, dict_without
)

from .sample_data import (
    DATASET_COLUMNS, DATASETS,
    DOCUMENT_COLUMNS, DOCUMENTS
)


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

        # Create a dataset
        dataset_kwargs = dict(zip(DATASET_COLUMNS, DATASETS[0]))
        dataset_mod_kwargs = dict_without(dataset_kwargs, 'id')
        dataset = db.datasets.create(**dataset_mod_kwargs)

        # Create a document
        document_kwargs = dict(zip(DOCUMENT_COLUMNS, DOCUMENTS[0]))
        document_mod_kwargs = modified_dict(document_kwargs, modifications)
        document = dataset.documents.create(**document_mod_kwargs)

        # Assert
        assert document.id == document_kwargs['id']
        assert document.recommended_citation == document_mod_kwargs['recommended_citation']
        assert document.extra == document_mod_kwargs.get('extra', None)

    INVALID_FIELD_DATA = {
        'id__given': (set_mods('id', value=99), ValueError),

        'recommended_citation__not_given':                 (delete_mods('id', 'recommended_citation'), TypeError),
        'recommended_citation__wrong_type__NoneType':      (delete_mods('id') + set_none_mods('recommended_citation'), TypeError),
        'recommended_citation__wrong_type__int':           (delete_mods('id') + set_mods('recommended_citation', value=99), TypeError),
        'recommended_citation__wrong_value__empty_string': (delete_mods('id') + set_mods('recommended_citation', value=''), ValueError),

        'extra__wrong_type__str':            (delete_mods('id') + set_mods('extra', value='Skittles'), TypeError),
        'extra__wrong_type__int':            (delete_mods('id') + set_mods('extra', value=99), TypeError),
        'extra__wrong_item_key_type__int':   (delete_mods('id') + set_mods('extra', value={844: 'Skittles', 'two_cat': 'Duchess'}), TypeError),
        'extra__wrong_item_value_type__int': (delete_mods('id') + set_mods('extra', value={'one_cat': 844, 'two_cat': 'Duchess'}),  TypeError),
    }

    @pytest.mark.parametrize('modifications, expected_exc', INVALID_FIELD_DATA.values(), ids=INVALID_FIELD_DATA.keys())
    def test_invalid(self, empty_db, modifications, expected_exc):
        db = empty_db

        # Create a dataset
        dataset_kwargs = dict(zip(DATASET_COLUMNS, DATASETS[0]))
        dataset_mod_kwargs = dict_without(dataset_kwargs, 'id')
        dataset = db.datasets.create(**dataset_mod_kwargs)

        # Create a document
        document_kwargs = dict(zip(DOCUMENT_COLUMNS, DOCUMENTS[0]))
        document_mod_kwargs = modified_dict(document_kwargs, modifications)

        with pytest.raises(expected_exc):
            dataset.documents.create(**document_mod_kwargs)

    def test_with_duplicate_recommended_citation(self, populated_db):
        dataset = populated_db.datasets.get_by_id(1)

        kwargs = dict(zip(DOCUMENT_COLUMNS, DOCUMENTS[0]))
        mod_kwargs = dict_without(kwargs, 'id')

        with pytest.raises(ValueError):
            dataset.documents.create(**mod_kwargs)


class TestGetByID:
    @pytest.mark.parametrize('kwargs', [dict(zip(DOCUMENT_COLUMNS, x)) for x in DOCUMENTS])
    def test_valid(self, populated_db, kwargs):
        dataset = populated_db.datasets.get_by_id(kwargs['dataset_id'])
        document = dataset.documents.get_by_id(kwargs['id'])

        assert document.id == kwargs['id']
        assert document.dataset_id == kwargs['dataset_id']
        assert document.recommended_citation == kwargs['recommended_citation']
        assert document.extra == kwargs['extra']

    INVALID_ID_DATA = {
        'wrong_type__str':      ('Skittles',),
        'wrong_type__NoneType': (None,),
        'wrong_type__dict':     ({'cat': 'Skittles'},),
    }

    @pytest.mark.parametrize('id', list(INVALID_ID_DATA.values()), ids=list(INVALID_ID_DATA.keys()))
    def test_invalid(self, empty_db, id):
        db = empty_db

        # Create a dataset
        dataset_kwargs = dict(zip(DATASET_COLUMNS, DATASETS[0]))
        dataset_mod_kwargs = dict_without(dataset_kwargs, 'id')
        dataset = db.datasets.create(**dataset_mod_kwargs)

        with pytest.raises(TypeError) as excinfo:
            dataset.documents.get_by_id(id)

    def test_non_existant(self, empty_db):
        db = empty_db

        # Create a dataset
        kwargs = dict(zip(DATASET_COLUMNS, DATASETS[0]))
        mod_kwargs = dict_without(kwargs, 'id')
        dataset = db.datasets.create(**mod_kwargs)

        document = dataset.documents.get_by_id(99)

        assert document is None


class TestGetByRecommendedCitation:
    @pytest.mark.parametrize('kwargs', [dict(zip(DOCUMENT_COLUMNS, x)) for x in DOCUMENTS])
    def test_valid(self, populated_db, kwargs):
        dataset = populated_db.datasets.get_by_id(kwargs['dataset_id'])

        document = dataset.documents.get_by_recommended_citation(kwargs['recommended_citation'])

        assert document.id == kwargs['id']
        assert document.dataset_id == kwargs['dataset_id']
        assert document.recommended_citation == kwargs['recommended_citation']
        assert document.extra == kwargs['extra']

    INVALID_RECOMMENDED_CITATION_DATA = {
        'wrong_type__int':      (8,),
        'wrong_type__NoneType': (None,),
        'wrong_type__dict':     ({'cat': 'Skittles'},),
    }

    @pytest.mark.parametrize('recommended_citation', list(INVALID_RECOMMENDED_CITATION_DATA.values()), ids=list(INVALID_RECOMMENDED_CITATION_DATA.keys()))
    def test_invalid(self, empty_db, recommended_citation):
        db = empty_db

        # Create a dataset
        dataset_kwargs = dict(zip(DATASET_COLUMNS, DATASETS[0]))
        dataset_mod_kwargs = dict_without(dataset_kwargs, 'id')
        dataset = db.datasets.create(**dataset_mod_kwargs)

        with pytest.raises(TypeError) as excinfo:
            dataset.documents.get_by_recommended_citation(recommended_citation)

    def test_non_existant(self, empty_db):
        db = empty_db

        # Create a dataset
        dataset_kwargs = dict(zip(DATASET_COLUMNS, DATASETS[0]))
        dataset_mod_kwargs = dict_without(dataset_kwargs, 'id')
        dataset = db.datasets.create(**dataset_mod_kwargs)

        document = dataset.documents.get_by_recommended_citation('test citation')
        assert document is None


class TestIter:
    def test_with_no_documents(self, empty_db):
        db = empty_db

        # Create a dataset
        dataset_kwargs = dict(zip(DATASET_COLUMNS, DATASETS[0]))
        dataset_mod_kwargs = dict_without(dataset_kwargs, 'id')
        dataset = db.datasets.create(**dataset_mod_kwargs)

        documents = list(dataset.documents)

        expected_documents = list()
        assert documents == expected_documents

    def test_with_populated_db(self, populated_db):
        dataset = populated_db.datasets.get_by_id(1)

        documents = list(dataset.documents)

        for idx, document in enumerate(documents):
            kwargs = dict(zip(DOCUMENT_COLUMNS, DOCUMENTS[idx]))

            assert document.id == kwargs['id']
            assert document.dataset_id == kwargs['dataset_id']
            assert document.recommended_citation == kwargs['recommended_citation']
            assert document.extra == kwargs['extra']
