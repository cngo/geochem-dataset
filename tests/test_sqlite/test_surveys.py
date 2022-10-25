from geochem_dataset.sqlite.models import Dataset
import pytest

from tests.helpers.utils import DeleteField
from tests.helpers.utils import kwargs_without_id
from tests.helpers.utils import modified_kwargs

from .sample_data import (
    DATASET_COLUMNS, DATASETS,
    SURVEY_COLUMNS, SURVEYS
)

DELETE_ID_FIELD = ('id', DeleteField)


class TestCreate:
    VALID_FIELD_DATA = {
        'id__not_given': [DELETE_ID_FIELD],
        'id__NoneType':  [('id', None)],

        'dataset_id__not_given': [DELETE_ID_FIELD, ('dataset_id', DeleteField)],
        'dataset_id__NoneType':  [DELETE_ID_FIELD, ('dataset_id', None)],

        'year_end__not_given': [DELETE_ID_FIELD, ('year_end', DeleteField)],
        'year_end__NoneType':  [DELETE_ID_FIELD, ('year_end', None)],

        'party_leader__not_given': [DELETE_ID_FIELD, ('party_leader', DeleteField)],
        'party_leader__NoneType':  [DELETE_ID_FIELD, ('party_leader', None)],
        'party_leader__empty':     [DELETE_ID_FIELD, ('party_leader', '')],

        'description__not_given': [DELETE_ID_FIELD, ('description', DeleteField)],
        'description__NoneType':  [DELETE_ID_FIELD, ('description', None)],
        'description__empty':     [DELETE_ID_FIELD, ('description', '')],

        'gsc_catalog_number__not_given': [DELETE_ID_FIELD, ('gsc_catalog_number', DeleteField)],
        'gsc_catalog_number__NoneType':  [DELETE_ID_FIELD, ('gsc_catalog_number', None)],

        'extra__not_given': [DELETE_ID_FIELD, ('extra', DeleteField)],
        'extra__NoneType':  [DELETE_ID_FIELD, ('extra', None)],
    }

    @pytest.mark.parametrize('modifications', VALID_FIELD_DATA.values(), ids=VALID_FIELD_DATA.keys())
    def test_valid(self, initialized_db, modifications):
        # Create a dataset
        dataset_kwargs = dict(zip(DATASET_COLUMNS, DATASETS[0]))
        dataset_mod_kwargs = modified_kwargs(dataset_kwargs, [DELETE_ID_FIELD])
        dataset = initialized_db.datasets.create(**dataset_mod_kwargs)

        # Create a survey
        survey_kwargs = dict(zip(SURVEY_COLUMNS, SURVEYS[0]))
        survey_mod_kwargs = modified_kwargs(survey_kwargs, modifications)
        survey = dataset.surveys.create(**survey_mod_kwargs)

        # Assert
        assert survey.id == survey_kwargs['id']
        assert survey.dataset_id == survey_kwargs['dataset_id']
        assert survey.title == survey_mod_kwargs['title']
        assert survey.organization == survey_mod_kwargs['organization']
        assert survey.year_begin == survey_mod_kwargs['year_begin']
        assert survey.year_end == survey_mod_kwargs.get('year_end', None)
        assert survey.party_leader == survey_mod_kwargs.get('party_leader', None)
        assert survey.description == survey_mod_kwargs.get('description', None)
        assert survey.gsc_catalog_number == survey_mod_kwargs.get('gsc_catalog_number', None)
        assert survey.extra == survey_mod_kwargs.get('extra', None)

    INVALID_FIELD_DATA = {
        'id__given': ([('id', 99)], ValueError),

        'dataset_id__given': ([('dataset_id', 99)], ValueError),

        'title__not_given':            ([DELETE_ID_FIELD, ('title', DeleteField)], TypeError),
        'title__wrong_type__NoneType': ([DELETE_ID_FIELD, ('title', None)], TypeError),
        'title__wrong_type__int':      ([DELETE_ID_FIELD, ('title', 99)], TypeError),
        'title__wrong_value__empty':   ([DELETE_ID_FIELD, ('title', '')], ValueError),

        'organization__not_given':            ([DELETE_ID_FIELD, ('organization', DeleteField)], TypeError),
        'organization__wrong_type__NoneType': ([DELETE_ID_FIELD, ('organization', None)], TypeError),
        'organization__wrong_type__int':      ([DELETE_ID_FIELD, ('organization', 99)], TypeError),
        'organization__wrong_value__empty':   ([DELETE_ID_FIELD, ('organization', '')], ValueError),

        'year_begin__not_given':            ([DELETE_ID_FIELD, ('year_begin', DeleteField)], TypeError),
        'year_begin__wrong_type__NoneType': ([DELETE_ID_FIELD, ('year_begin', None)], TypeError),
        'year_begin__wrong_type__str':      ([DELETE_ID_FIELD, ('year_begin', 'Skittles')], TypeError),

        'year_end__wrong_type__str':         ([DELETE_ID_FIELD, ('year_end', 'Skittles')], TypeError),
        'year_end__earlier_than_year_begin': ([DELETE_ID_FIELD, ('year_begin', 2021), ('year_end', 1999)], ValueError),

        'party_leader__wrong_type__int': ([DELETE_ID_FIELD, ('party_leader', 99)], TypeError),

        'description__wrong_type__int': ([DELETE_ID_FIELD, ('description', 99)], TypeError),

        'gsc_catalog_number__wrong_type__str': ([DELETE_ID_FIELD, ('gsc_catalog_number', 'Skittles')], TypeError),

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

        # Create a survey
        survey_kwargs = dict(zip(SURVEY_COLUMNS, SURVEYS[0]))
        survey_mod_kwargs = modified_kwargs(survey_kwargs, modifications)

        with pytest.raises(expected_exc):
            dataset.surveys.create(**survey_mod_kwargs)

    def test_with_duplicate_title(self, populated_db):
        dataset = populated_db.datasets.get_by_id(1)

        kwargs = dict(zip(SURVEY_COLUMNS, SURVEYS[0]))
        mod_kwargs = kwargs_without_id(kwargs)

        with pytest.raises(ValueError):
            dataset.surveys.create(**mod_kwargs)


class TestGetByID:
    @pytest.mark.parametrize('kwargs', [dict(zip(SURVEY_COLUMNS, x)) for x in SURVEYS])
    def test_valid(self, populated_db, kwargs):
        dataset = populated_db.datasets.get_by_id(kwargs['dataset_id'])
        survey = dataset.surveys.get_by_id(kwargs['id'])

        assert survey.id == kwargs['id']
        assert survey.dataset_id == kwargs['dataset_id']
        assert survey.title == kwargs['title']
        assert survey.organization == kwargs['organization']
        assert survey.year_begin == kwargs['year_begin']
        assert survey.year_end == kwargs['year_end']
        assert survey.party_leader == kwargs['party_leader']
        assert survey.description == kwargs['description']
        assert survey.gsc_catalog_number == kwargs['gsc_catalog_number']
        assert survey.extra == kwargs['extra']


    INVALID_ID_DATA = {
        'wrong_type__str':      ('Skittles',),
        'wrong_type__NoneType': (None,),
        'wrong_type__dict':     ({'cat': 'Skittles'},),
    }

    @pytest.mark.parametrize('id', list(INVALID_ID_DATA.values()), ids=list(INVALID_ID_DATA.keys()))
    def test_invalid(self, initialized_db, id):
        # Create a dataset
        dataset_kwargs = dict(zip(DATASET_COLUMNS, DATASETS[0]))
        dataset_mod_kwargs = kwargs_without_id(dataset_kwargs)
        dataset = initialized_db.datasets.create(**dataset_mod_kwargs)

        with pytest.raises(TypeError) as excinfo:
            dataset.surveys.get_by_id(id)

    def test_non_existant(self, initialized_db):
        # Create a dataset
        dataset_kwargs = dict(zip(DATASET_COLUMNS, DATASETS[0]))
        dataset_mod_kwargs = kwargs_without_id(dataset_kwargs)
        dataset = initialized_db.datasets.create(**dataset_mod_kwargs)

        survey = dataset.surveys.get_by_id(99)

        assert survey is None


class TestGetByTitle:
    @pytest.mark.parametrize('kwargs', [dict(zip(SURVEY_COLUMNS, x)) for x in SURVEYS])
    def test_valid(self, populated_db, kwargs):
        dataset = populated_db.datasets.get_by_id(kwargs['dataset_id'])

        survey = dataset.surveys.get_by_title(kwargs['title'])

        assert survey.id == kwargs['id']
        assert survey.dataset_id == kwargs['dataset_id']
        assert survey.title == kwargs['title']
        assert survey.organization == kwargs['organization']
        assert survey.year_begin == kwargs['year_begin']
        assert survey.year_end == kwargs['year_end']
        assert survey.party_leader == kwargs['party_leader']
        assert survey.description == kwargs['description']
        assert survey.gsc_catalog_number == kwargs['gsc_catalog_number']
        assert survey.extra == kwargs['extra']

    INVALID_TITLE_DATA = {
        'wrong_type__int':      (8,),
        'wrong_type__NoneType': (None,),
        'wrong_type__dict':     ({'cat': 'Skittles'},),
    }

    @pytest.mark.parametrize('title', list(INVALID_TITLE_DATA.values()), ids=list(INVALID_TITLE_DATA.keys()))
    def test_invalid(self, initialized_db, title):
        # Create a dataset
        dataset_kwargs = dict(zip(DATASET_COLUMNS, DATASETS[0]))
        dataset_mod_kwargs = kwargs_without_id(dataset_kwargs)
        dataset = initialized_db.datasets.create(**dataset_mod_kwargs)

        with pytest.raises(TypeError) as excinfo:
            dataset.surveys.get_by_title(title)

    def test_non_existant(self, initialized_db):
        # Create a dataset
        dataset_kwargs = dict(zip(DATASET_COLUMNS, DATASETS[0]))
        dataset_mod_kwargs = kwargs_without_id(dataset_kwargs)
        dataset = initialized_db.datasets.create(**dataset_mod_kwargs)

        survey = dataset.surveys.get_by_title('Skittles')
        assert survey is None


class TestIter:
    def test_with_no_surveys(self, initialized_db):
        # Create a dataset
        dataset_kwargs = dict(zip(DATASET_COLUMNS, DATASETS[0]))
        dataset_mod_kwargs = kwargs_without_id(dataset_kwargs)
        dataset = initialized_db.datasets.create(**dataset_mod_kwargs)

        surveys = list(dataset.surveys)

        expected_surveys = list()
        assert surveys == expected_surveys

    def test_with_populated_db(self, populated_db):
        dataset = populated_db.datasets.get_by_id(1)

        surveys = list(dataset.surveys)

        for idx, survey in enumerate(surveys):
            kwargs = dict(zip(SURVEY_COLUMNS, SURVEYS[idx]))

            assert survey.id == kwargs['id']
            assert survey.dataset_id == kwargs['dataset_id']
            assert survey.title == kwargs['title']
            assert survey.organization == kwargs['organization']
            assert survey.year_begin == kwargs['year_begin']
            assert survey.year_end == kwargs['year_end']
            assert survey.party_leader == kwargs['party_leader']
            assert survey.description == kwargs['description']
            assert survey.gsc_catalog_number == kwargs['gsc_catalog_number']
            assert survey.extra == kwargs['extra']
