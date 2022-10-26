import pytest

from tests.helpers.utils import (
    DICT_MOD_SET, DICT_MOD_DELETE,
    DictMod, set_mods, set_none_mods, delete_mods,
    modified_dict, dict_without
)

from .sample_data import (
    DATASET_COLUMNS, DATASETS,
    SURVEY_COLUMNS, SURVEYS
)


class TestCreate:
    VALID_FIELD_DATA = {
        'id__not_given': delete_mods('id'),
        'id__NoneType':  set_none_mods('id'),

        'dataset_id__not_given': delete_mods('id', 'dataset_id'),
        'dataset_id__NoneType':  delete_mods('id') + set_none_mods('dataset_id'),

        'year_end__not_given': delete_mods('id', 'year_end'),
        'year_end__NoneType':  delete_mods('id') + set_none_mods('year_end'),

        'party_leader__not_given': delete_mods('id', 'party_leader'),
        'party_leader__NoneType':  delete_mods('id') + set_none_mods('party_leader'),
        'party_leader__empty':     delete_mods('id') + [DictMod('party_leader', DICT_MOD_SET, '')],

        'description__not_given': delete_mods('id', 'description'),
        'description__NoneType':  delete_mods('id') + set_none_mods('description'),
        'description__empty':     delete_mods('id') + set_mods('description', value=''),

        'gsc_catalog_number__not_given': delete_mods('id', 'gsc_catalog_number'),
        'gsc_catalog_number__NoneType':  delete_mods('id') + set_none_mods('gsc_catalog_number'),

        'extra__not_given': delete_mods('id', 'extra'),
        'extra__NoneType':  delete_mods('id') + set_none_mods('extra'),
    }

    @pytest.mark.parametrize('modifications', VALID_FIELD_DATA.values(), ids=VALID_FIELD_DATA.keys())
    def test_valid(self, empty_db, modifications):
        db = empty_db

        # Create a dataset
        dataset_kwargs = dict(zip(DATASET_COLUMNS, DATASETS[0]))
        dataset_mod_kwargs = modified_dict(dataset_kwargs, delete_mods('id'))
        dataset = db.datasets.create(**dataset_mod_kwargs)

        # Create a survey
        survey_kwargs = dict(zip(SURVEY_COLUMNS, SURVEYS[0]))
        survey_mod_kwargs = modified_dict(survey_kwargs, modifications)
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
        'id__given': ([('id', DICT_MOD_SET, 99)], ValueError),

        'dataset_id__given': ([DictMod('dataset_id', DICT_MOD_SET, 99)], ValueError),

        'title__not_given':            (delete_mods('id', 'title'), TypeError),
        'title__wrong_type__NoneType': (delete_mods('id') + set_none_mods('title'), TypeError),
        'title__wrong_type__int':      (delete_mods('id') + [DictMod('title', DICT_MOD_SET, 99)], TypeError),
        'title__wrong_value__empty':   (delete_mods('id') + [DictMod('title', DICT_MOD_SET, '')], ValueError),

        'organization__not_given':            (delete_mods('id', 'organization'), TypeError),
        'organization__wrong_type__NoneType': (delete_mods('id') + set_none_mods('organization'), TypeError),
        'organization__wrong_type__int':      (delete_mods('id') + [DictMod('organization', DICT_MOD_SET, 99)], TypeError),
        'organization__wrong_value__empty':   (delete_mods('id') + [DictMod('organization', DICT_MOD_SET, '')], ValueError),

        'year_begin__not_given':            (delete_mods('id', 'year_begin'), TypeError),
        'year_begin__wrong_type__NoneType': (delete_mods('id') + set_none_mods('year_begin'), TypeError),
        'year_begin__wrong_type__str':      (delete_mods('id') + [DictMod('year_begin', DICT_MOD_SET, 'Skittles')], TypeError),

        'year_end__wrong_type__str':         (delete_mods('id') + [DictMod('year_end', DICT_MOD_SET, 'Skittles')], TypeError),
        'year_end__earlier_than_year_begin': (delete_mods('id') + [DictMod('year_begin', DICT_MOD_SET, 2021), DictMod('year_end', DICT_MOD_SET, 1999)], ValueError),

        'party_leader__wrong_type__int': (delete_mods('id') + [DictMod('party_leader', DICT_MOD_SET, 99)], TypeError),

        'description__wrong_type__int': (delete_mods('id') + [DictMod('description', DICT_MOD_SET, 99)], TypeError),

        'gsc_catalog_number__wrong_type__str': (delete_mods('id') + [DictMod('gsc_catalog_number', DICT_MOD_SET, 'Skittles')], TypeError),

        'extra__wrong_type__str':            (delete_mods('id') + [DictMod('extra', DICT_MOD_SET, 'Skittles')], TypeError),
        'extra__wrong_type__int':            (delete_mods('id') + [DictMod('extra', DICT_MOD_SET, 99)], TypeError),
        'extra__wrong_item_key_type__int':   (delete_mods('id') + [DictMod('extra', DICT_MOD_SET, {844: 'Skittles', 'two_cat': 'Duchess'})], TypeError),
        'extra__wrong_item_value_type__int': (delete_mods('id') + [DictMod('extra', DICT_MOD_SET, {'one_cat': 844, 'two_cat': 'Duchess'})],  TypeError),
    }

    @pytest.mark.parametrize('modifications, expected_exc', INVALID_FIELD_DATA.values(), ids=INVALID_FIELD_DATA.keys())
    def test_invalid(self, empty_db, modifications, expected_exc):
        db = empty_db

        # Create a dataset
        dataset_kwargs = dict(zip(DATASET_COLUMNS, DATASETS[0]))
        dataset_mod_kwargs = modified_dict(dataset_kwargs, delete_mods('id'))
        dataset = db.datasets.create(**dataset_mod_kwargs)

        # Create a survey
        survey_kwargs = dict(zip(SURVEY_COLUMNS, SURVEYS[0]))
        survey_mod_kwargs = modified_dict(survey_kwargs, modifications)

        with pytest.raises(expected_exc):
            dataset.surveys.create(**survey_mod_kwargs)

    def test_with_duplicate_title(self, populated_db):
        dataset = populated_db.datasets.get_by_id(1)

        kwargs = dict(zip(SURVEY_COLUMNS, SURVEYS[0]))
        mod_kwargs = modified_dict(kwargs, delete_mods('id'))

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
    def test_invalid(self, empty_db, id):
        db = empty_db

        # Create a dataset
        dataset_kwargs = dict(zip(DATASET_COLUMNS, DATASETS[0]))
        dataset_mod_kwargs = dict_without(dataset_kwargs, 'id')
        dataset = db.datasets.create(**dataset_mod_kwargs)

        with pytest.raises(TypeError) as excinfo:
            dataset.surveys.get_by_id(id)

    def test_non_existant(self, empty_db):
        db = empty_db

        # Create a dataset
        dataset_kwargs = dict(zip(DATASET_COLUMNS, DATASETS[0]))
        dataset_mod_kwargs = dict_without(dataset_kwargs, 'id')
        dataset = db.datasets.create(**dataset_mod_kwargs)

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
    def test_invalid(self, empty_db, title):
        db = empty_db

        # Create a dataset
        dataset_kwargs = dict(zip(DATASET_COLUMNS, DATASETS[0]))
        dataset_mod_kwargs = dict_without(dataset_kwargs, 'id')
        dataset = db.datasets.create(**dataset_mod_kwargs)

        with pytest.raises(TypeError) as excinfo:
            dataset.surveys.get_by_title(title)

    def test_non_existant(self, empty_db):
        db = empty_db

        # Create a dataset
        dataset_kwargs = dict(zip(DATASET_COLUMNS, DATASETS[0]))
        dataset_mod_kwargs = dict_without(dataset_kwargs, 'id')
        dataset = db.datasets.create(**dataset_mod_kwargs)

        survey = dataset.surveys.get_by_title('Skittles')
        assert survey is None


class TestIter:
    def test_with_no_surveys(self, empty_db):
        db = empty_db

        # Create a dataset
        dataset_kwargs = dict(zip(DATASET_COLUMNS, DATASETS[0]))
        dataset_mod_kwargs = dict_without(dataset_kwargs, 'id')
        dataset = db.datasets.create(**dataset_mod_kwargs)

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
