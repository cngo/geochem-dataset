from geochem_dataset.sqlite.models import Dataset
import pytest

from tests.helpers.utils import DeleteField, kwargs_without_id, modified_kwargs
from .sample_data import (
    DATASET_COLUMNS, DATASETS,
    DOCUMENT_COLUMNS, DOCUMENTS
)

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
        # Create a dataset
        dataset_kwargs = dict(zip(DATASET_COLUMNS, DATASETS[0]))
        dataset_mod_kwargs = modified_kwargs(dataset_kwargs, [DELETE_ID_FIELD])
        dataset = initialized_db.datasets.create(**dataset_mod_kwargs)

        # Create a document
        document_kwargs = dict(zip(DOCUMENT_COLUMNS, DOCUMENTS[0]))
        document_mod_kwargs = modified_kwargs(document_kwargs, modifications)
        document = dataset.documents.create(**document_mod_kwargs)

        # Assert
        assert document.id == document_kwargs['id']
        assert document.recommended_citation == document_mod_kwargs['recommended_citation']
        assert document.extra == document_mod_kwargs.get('extra', None)

    INVALID_FIELD_DATA = {
        'id__given': ([('id', 99)], ValueError),

        'recommended_citation__not_given':                 ([DELETE_ID_FIELD, ('recommended_citation', DeleteField)], TypeError),
        'recommended_citation__wrong_type__NoneType':      ([DELETE_ID_FIELD, ('recommended_citation', None)], TypeError),
        'recommended_citation__wrong_type__int':           ([DELETE_ID_FIELD, ('recommended_citation', 99)], TypeError),
        'recommended_citation__wrong_value__empty_string': ([DELETE_ID_FIELD, ('recommended_citation', '')], ValueError),

        'extra__wrong_type__str':            ([DELETE_ID_FIELD, ('extra', 'Skittles')], TypeError),
        'extra__wrong_type__int':            ([DELETE_ID_FIELD, ('extra', 99)], TypeError),
        'extra__wrong_item_key_type__int':   ([DELETE_ID_FIELD, ('extra', {844: 'Skittles', 'two_cat': 'Duchess'})], TypeError),
        'extra__wrong_item_value_type__int': ([DELETE_ID_FIELD, ('extra', {'one_cat': 844, 'two_cat': 'Duchess'})],  TypeError),
    }

    @pytest.mark.parametrize('modifications, expected_exc', INVALID_FIELD_DATA.values(), ids=INVALID_FIELD_DATA.keys())
    def test_invalid(self, initialized_db, modifications, expected_exc):
        # Create a dataset
        dataset_kwargs = dict(zip(DATASET_COLUMNS, DATASETS[0]))
        dataset_mod_kwargs = modified_kwargs(dataset_kwargs, [DELETE_ID_FIELD])
        dataset = initialized_db.datasets.create(**dataset_mod_kwargs)

        # Create a document
        document_kwargs = dict(zip(DOCUMENT_COLUMNS, DOCUMENTS[0]))
        document_mod_kwargs = modified_kwargs(document_kwargs, modifications)

        with pytest.raises(expected_exc):
            dataset.documents.create(**document_mod_kwargs)

    def test_with_duplicate_recommended_citation(self, populated_db):
        dataset = populated_db.datasets.get_by_id(1)

        kwargs = dict(zip(DOCUMENT_COLUMNS, DOCUMENTS[0]))
        mod_kwargs = kwargs_without_id(kwargs)

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
    def test_invalid(self, initialized_db, id):
        # Create a dataset
        dataset_kwargs = dict(zip(DATASET_COLUMNS, DATASETS[0]))
        dataset_mod_kwargs = modified_kwargs(dataset_kwargs, [DELETE_ID_FIELD])
        dataset = initialized_db.datasets.create(**dataset_mod_kwargs)

        with pytest.raises(TypeError) as excinfo:
            dataset.documents.get_by_id(id)

    def test_non_existant(self, initialized_db):
        # Create a dataset
        dataset_kwargs = dict(zip(DATASET_COLUMNS, DATASETS[0]))
        dataset_mod_kwargs = modified_kwargs(dataset_kwargs, [DELETE_ID_FIELD])
        dataset = initialized_db.datasets.create(**dataset_mod_kwargs)

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
    def test_invalid(self, initialized_db, recommended_citation):
        # Create a dataset
        dataset_kwargs = dict(zip(DATASET_COLUMNS, DATASETS[0]))
        dataset_mod_kwargs = modified_kwargs(dataset_kwargs, [DELETE_ID_FIELD])
        dataset = initialized_db.datasets.create(**dataset_mod_kwargs)

        with pytest.raises(TypeError) as excinfo:
            dataset.documents.get_by_recommended_citation(recommended_citation)

    def test_non_existant(self, initialized_db):
        # Create a dataset
        dataset_kwargs = dict(zip(DATASET_COLUMNS, DATASETS[0]))
        dataset_mod_kwargs = modified_kwargs(dataset_kwargs, [DELETE_ID_FIELD])
        dataset = initialized_db.datasets.create(**dataset_mod_kwargs)

        document = dataset.documents.get_by_recommended_citation('test citation')
        assert document is None


class TestIter:
    def test_with_no_documents(self, initialized_db):
        # Create a dataset
        dataset_kwargs = dict(zip(DATASET_COLUMNS, DATASETS[0]))
        dataset_mod_kwargs = modified_kwargs(dataset_kwargs, [DELETE_ID_FIELD])
        dataset = initialized_db.datasets.create(**dataset_mod_kwargs)

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
