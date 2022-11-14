from decimal import Decimal

import pytest

from tests.helpers.utils import (
    DICT_MOD_SET, DICT_MOD_DELETE,
    DictMod, set_mods, set_none_mods, delete_mods,
    modified_dict, dict_without
)

from .sample_data import (
    DATASET_COLUMNS, DATASETS,
    SURVEY_COLUMNS, SURVEYS,
    SAMPLE_COLUMNS, SAMPLES
)


class TestCreate:
    VALID_FIELD_DATA = {
        'id__not_given': delete_mods('id'),
        'id__NoneType':  set_none_mods('id'),

        'survey_id__not_given': delete_mods('id', 'survey_id'),
        'survey_id__NoneType':  delete_mods('id') + set_none_mods('survey_id'),

        'lat_and_long_nad27__not_given': delete_mods('id', 'lat_nad27', 'long_nad27'),
        'lat_and_long_nad27__NoneType':  delete_mods('id') + set_none_mods('lat_nad27', 'long_nad27'),
        'lat_and_long_nad83__not_given': delete_mods('id', 'lat_nad83', 'long_nad83'),
        'lat_and_long_nad83__NoneType':  delete_mods('id') + set_none_mods('lat_nad83', 'long_nad83'),

        'x_and_y_nad27__not_given': delete_mods('id', 'x_nad27', 'y_nad27'),
        'x_and_y_nad27__NoneType':  delete_mods('id') + set_none_mods('x_nad27', 'y_nad27'),
        'x_and_y_nad83__not_given': delete_mods('id', 'x_nad83', 'y_nad83'),
        'x_and_y_nad83__NoneType':  delete_mods('id') + set_none_mods('x_nad83', 'y_nad83'),

        'x_and_y_nad27_and_nad83_and_zone__not_given': delete_mods('id', 'x_nad27', 'y_nad27', 'x_nad83', 'y_nad83', 'zone'),
        'x_and_y_nad27_and_nad83_and_zone__NoneType':  delete_mods('id') + set_none_mods('x_nad27', 'y_nad27', 'x_nad83', 'y_nad83', 'zone'),

        'earthmat_type__not_given': delete_mods('id', 'earthmat_type'),
        'earthmat_type__NoneType':  delete_mods('id') + set_none_mods('earthmat_type'),

        'status__not_given': delete_mods('id', 'status'),
        'status__NoneType':  delete_mods('id') + set_none_mods('status'),

        'extra__not_given': delete_mods('id', 'extra'),
        'extra__NoneType':  delete_mods('id') + set_none_mods('extra'),
    }

    @pytest.mark.parametrize('mods', VALID_FIELD_DATA.values(), ids=VALID_FIELD_DATA.keys())
    def test_valid(self, empty_db, mods):
        db = empty_db

        # Create a dataset
        dataset_kwargs = dict(zip(DATASET_COLUMNS, DATASETS[0]))
        dataset_mod_kwargs = dict_without(dataset_kwargs, 'id')
        dataset = db.datasets.create(**dataset_mod_kwargs)

        # Create a survey
        survey_kwargs = dict(zip(SURVEY_COLUMNS, SURVEYS[0]))
        survey_mod_kwargs = dict_without(survey_kwargs, 'id')
        survey = dataset.surveys.create(**survey_mod_kwargs)

        # Create a sample
        sample_kwargs = dict(zip(SAMPLE_COLUMNS, SAMPLES[0]))
        sample_mod_kwargs = modified_dict(sample_kwargs, mods)

        sample = survey.samples.create(**sample_mod_kwargs)

        assert sample.id == sample_kwargs['id']
        assert sample.survey_id == sample_kwargs['survey_id']
        assert sample.station == sample_kwargs['station']
        assert sample.earthmat == sample_kwargs['earthmat']
        assert sample.name == sample_kwargs['name']
        assert sample.lat_nad27 == sample_mod_kwargs.get('lat_nad27', None)
        assert sample.long_nad27 == sample_mod_kwargs.get('long_nad27', None)
        assert sample.lat_nad83 == sample_mod_kwargs.get('lat_nad83', None)
        assert sample.long_nad83 == sample_mod_kwargs.get('long_nad83', None)
        assert sample.x_nad27 == sample_mod_kwargs.get('x_nad27', None)
        assert sample.y_nad27 == sample_mod_kwargs.get('y_nad27', None)
        assert sample.x_nad83 == sample_mod_kwargs.get('x_nad83', None)
        assert sample.y_nad83 == sample_mod_kwargs.get('y_nad83', None)
        assert sample.zone == sample_mod_kwargs.get('zone', None)
        assert sample.earthmat_type == sample_mod_kwargs.get('earthmat_type', None)
        assert sample.status == sample_mod_kwargs.get('status', None)
        assert sample.extra == sample_mod_kwargs.get('extra', None)

    INVALID_FIELD_DATA = {
        'id__given': (set_mods('id', value=99), ValueError),

        'survey_id__given': (set_mods('survey_id', value=99), ValueError),

        'station__not_given':            (delete_mods('id', 'station'), TypeError),
        'station__wrong_type__NoneType': (delete_mods('id') + set_none_mods('station'), TypeError),
        'station__wrong_type__int':      (delete_mods('id') + set_mods('station', value=99), TypeError),
        'station__wrong_value__empty':   (delete_mods('id') + set_mods('station', value=''), ValueError),

        'earthmat__not_given':            (delete_mods('id', 'earthmat'), TypeError),
        'earthmat__wrong_type__NoneType': (delete_mods('id') + set_none_mods('earthmat'), TypeError),
        'earthmat__wrong_type__int':      (delete_mods('id') + set_mods('earthmat', value=99), TypeError),
        'earthmat__wrong_value__empty':   (delete_mods('id') + set_mods('earthmat', value=''), ValueError),

        'name__not_given':            (delete_mods('id', 'name'), TypeError),
        'name__wrong_type__NoneType': (delete_mods('id') + set_none_mods('name'), TypeError),
        'name__wrong_type__int':      (delete_mods('id') + set_mods('name', value=99), TypeError),
        'name__wrong_value__empty':   (delete_mods('id') + set_mods('name', value=''), ValueError),

        'lat_nad27__wrong_type__str':  (delete_mods('id') + set_mods('lat_nad27', value='Skittles'), TypeError),
        'lat_nad27__wrong_type__int':  (delete_mods('id') + set_mods('lat_nad27', value=50), TypeError),
        'lat_nad27__invalid_value':    (delete_mods('id') + set_mods('lat_nad27', value=99.0), ValueError),
        'long_nad27__wrong_type__str': (delete_mods('id') + set_mods('long_nad27', value='Skittles'), TypeError),
        'long_nad27__wrong_type__int': (delete_mods('id') + set_mods('long_nad27', value=100), TypeError),
        'long_nad27__invalid_value':   (delete_mods('id') + set_mods('long_nad27', value=189.0), ValueError),

        'lat_nad27__given__long_nad27__not_given': (delete_mods('id', 'long_nad27') + set_mods('lat_nad27', value=90.0), ValueError),
        'lat_nad27__given__long_nad27__NoneType':  (delete_mods('id') + set_mods('lat_nad27', value=90.0) + set_none_mods('long_nad27'), ValueError),
        'lat_nad27__not_given__long_nad27__given': (delete_mods('id', 'lat_nad27') + set_mods('long_nad27', value=180.0), ValueError),
        'lat_nad27__NoneType__long_nad27_given':   (delete_mods('id') + set_none_mods('lat_nad27') + set_mods('long_nad27', value=180.0), ValueError),

        'lat_nad83__wrong_type__str':  (delete_mods('id') + set_mods('lat_nad83', value='Skittles'), TypeError),
        'lat_nad83__wrong_type__int':  (delete_mods('id') + set_mods('lat_nad83', value=50), TypeError),
        'lat_nad83__invalid_value':    (delete_mods('id') + set_mods('lat_nad83', value=99.0), ValueError),
        'long_nad83__wrong_type__str': (delete_mods('id') + set_mods('long_nad83', value='Skittles'), TypeError),
        'long_nad83__wrong_type__int': (delete_mods('id') + set_mods('long_nad83', value=100), TypeError),
        'long_nad83__invalid_value':   (delete_mods('id') + set_mods('long_nad83', value=189.0), ValueError),

        'lat_nad83__given__long_nad83__not_given': (delete_mods('id', 'long_nad83') + set_mods('lat_nad83', value=90.0), ValueError),
        'lat_nad83__given__long_nad83__NoneType':  (delete_mods('id') + set_mods('lat_nad83', value=90.0) + set_none_mods('long_nad83'), ValueError),
        'lat_nad83__not_given__long_nad83__given': (delete_mods('id', 'lat_nad83') + set_mods('long_nad83', value=180.0), ValueError),
        'lat_nad83__NoneType__long_nad83_given':   (delete_mods('id') + set_none_mods('lat_nad83') + set_mods('long_nad83', value=180.0), ValueError),

        'x_nad27__wrong_type__str':              (delete_mods('id') + set_mods('x_nad27', value='Skittles'), TypeError),
        'x_nad27__wrong_type__int':              (delete_mods('id') + set_mods('x_nad27', value=99), TypeError),
        # 'x_nad27__invalid_value__-99.0':         (delete_mods('id') + set_mods('x_nad27', value=-99.0), ValueError),
        # 'x_nad27__invalid_value__0.0':           (delete_mods('id') + set_mods('x_nad27', value=0.0), ValueError),
        # 'x_nad27__invalid_value__1000000.0':     (delete_mods('id') + set_mods('x_nad27', value=1000000.0), ValueError),
        # 'x_nad27__invalid_value__1000000.1':     (delete_mods('id') + set_mods('x_nad27', value=1000000.1), ValueError),
        'y_nad27__wrong_type__str':              (delete_mods('id') + set_mods('y_nad27', value='Skittles'), TypeError),
        'y_nad27__wrong_type__int':              (delete_mods('id') + set_mods('y_nad27', value=99), TypeError),
        # 'y_nad27__invalid_value__-99.0':         (delete_mods('id') + set_mods('y_nad27', value=-99.0), ValueError),
        # 'y_nad27__invalid_value__0.0':           (delete_mods('id') + set_mods('y_nad27', value=0.0), ValueError),
        # 'y_nad27__invalid_value__10000000000.0': (delete_mods('id') + set_mods('y_nad27', value=10000000000.0), ValueError),

        'x_nad27__given__y_nad27__not_given': (delete_mods('id', 'y_nad27') + set_mods('x_nad27', value=22.0), ValueError),
        'x_nad27__given__y_nad27__NoneType':  (delete_mods('id') + set_mods('x_nad27', value=22.0) + set_none_mods('y_nad27'), ValueError),
        'x_nad27__not_given__y_nad27__given': (delete_mods('id', 'x_nad27') + set_mods('y_nad27', value=22.0), ValueError),
        'x_nad27__NoneType__y_nad27_given':   (delete_mods('id') + set_none_mods('x_nad27') + set_mods('y_nad27', value=22.0), ValueError),

        'x_nad83__wrong_type__str':              (delete_mods('id') + set_mods('x_nad83', value='Skittles'), TypeError),
        'x_nad83__wrong_type__int':              (delete_mods('id') + set_mods('x_nad83', value=99), TypeError),
        # 'x_nad83__invalid_value__-99.0':         (delete_mods('id') + set_mods('x_nad83', value=-99.0), ValueError),
        # 'x_nad83__invalid_value__0.0':           (delete_mods('id') + set_mods('x_nad83', value=0.0), ValueError),
        # 'x_nad83__invalid_value__1000000.0':     (delete_mods('id') + set_mods('x_nad83', value=1000000.0), ValueError),
        # 'x_nad83__invalid_value__1000000.1':     (delete_mods('id') + set_mods('x_nad83', value=1000000.1), ValueError),
        'y_nad83__wrong_type__str':              (delete_mods('id') + set_mods('y_nad83', value='Skittles'), TypeError),
        'y_nad83__wrong_type__int':              (delete_mods('id') + set_mods('y_nad83', value=99), TypeError),
        # 'y_nad83__invalid_value__-99.0':         (delete_mods('id') + set_mods('y_nad83', value=-99.0), ValueError),
        # 'y_nad83__invalid_value__0.0':           (delete_mods('id') + set_mods('y_nad83', value=0.0), ValueError),
        # 'y_nad83__invalid_value__10000000000.0': (delete_mods('id') + set_mods('y_nad83', value=10000000000.0), ValueError),

        'x_nad83__given__y_nad83__not_given': (delete_mods('id', 'y_nad83') + set_mods('x_nad83', value=22.0), ValueError),
        'x_nad83__given__y_nad83__NoneType':  (delete_mods('id') + set_mods('x_nad83', value=22.0) + set_none_mods('y_nad83'), ValueError),
        'x_nad83__not_given__y_nad83__given': (delete_mods('id', 'x_nad83') + set_mods('y_nad83', value=22.0), ValueError),
        'x_nad83__NoneType__y_nad83_given':   (delete_mods('id') + set_none_mods('x_nad83') + set_mods('y_nad83', value=22.0), ValueError),

        'zone__wrong_type__int': (delete_mods('id') + set_mods('zone', value=99), TypeError),
        'zone__empty':           (delete_mods('id') + set_mods('zone', value=''), ValueError),

        'earthmat_type__wrong_type__int': (delete_mods('id') + set_mods('earthmat_type', value=99), TypeError),
        'earthmat_type__empty':           (delete_mods('id') + set_mods('earthmat_type', value=''), ValueError),

        'status__wrong_type__int': (delete_mods('id') + set_mods('status', value=99), TypeError),
        'status__empty':           (delete_mods('id') + set_mods('status', value=''), ValueError),

        'extra__wrong_type__str':            (delete_mods('id') + set_mods('extra', value='Skittles'), TypeError),
        'extra__wrong_type__int':            (delete_mods('id') + set_mods('extra', value=99), TypeError),
        'extra__wrong_item_key_type__int':   (delete_mods('id') + set_mods('extra', value={99: 'Skittles'}), TypeError),
        'extra__wrong_item_value_type__int': (delete_mods('id') + set_mods('extra', value={'cat': 99}),  TypeError),
    }

    @pytest.mark.parametrize('mods, expected_exc', INVALID_FIELD_DATA.values(), ids=INVALID_FIELD_DATA.keys())
    def test_invalid(self, empty_db, mods, expected_exc):
        db = empty_db

        # Create a dataset
        dataset_kwargs = dict(zip(DATASET_COLUMNS, DATASETS[0]))
        dataset_mod_kwargs = dict_without(dataset_kwargs, 'id')
        dataset = db.datasets.create(**dataset_mod_kwargs)

        # Create a survey
        survey_kwargs = dict(zip(SURVEY_COLUMNS, SURVEYS[0]))
        survey_mod_kwargs = dict_without(survey_kwargs, 'id')
        survey = dataset.surveys.create(**survey_mod_kwargs)

        # Create a sample
        sample_kwargs = dict(zip(SAMPLE_COLUMNS, SAMPLES[0]))
        sample_mod_kwargs = modified_dict(sample_kwargs, mods)

        with pytest.raises(expected_exc):
            survey.samples.create(**sample_mod_kwargs)

    def test_with_duplicate_station_earthmat_name(self, populated_db):
        db = populated_db

        dataset = db.datasets.get_by_id(1)
        survey = dataset.surveys.get_by_id(1)

        kwargs = dict(zip(SAMPLE_COLUMNS, SAMPLES[0]))
        mod_kwargs = dict_without(kwargs, 'id')

        with pytest.raises(ValueError):
            survey.samples.create(**mod_kwargs)


class TestGetByID:
    @pytest.mark.parametrize('kwargs', [dict(zip(SAMPLE_COLUMNS, x)) for x in SAMPLES])
    def test_valid(self, populated_db, kwargs):
        db = populated_db

        dataset = db.datasets.get_by_id(1)
        survey = dataset.surveys.get_by_id(kwargs['survey_id'])
        sample = survey.samples.get_by_id(kwargs['id'])

        assert sample.id == kwargs['id']
        assert sample.survey_id == kwargs['survey_id']
        assert sample.station == kwargs['station']
        assert sample.earthmat == kwargs['earthmat']
        assert sample.name == kwargs['name']
        assert sample.lat_nad27 == kwargs['lat_nad27']
        assert sample.long_nad27 == kwargs['long_nad27']
        assert sample.lat_nad83 == kwargs['lat_nad83']
        assert sample.long_nad83 == kwargs['long_nad83']
        assert sample.x_nad27 == kwargs['x_nad27']
        assert sample.y_nad27 == kwargs['y_nad27']
        assert sample.x_nad83 == kwargs['x_nad83']
        assert sample.y_nad83 == kwargs['y_nad83']
        assert sample.zone == kwargs['zone']
        assert sample.earthmat_type == kwargs['earthmat_type']
        assert sample.status == kwargs['status']
        assert sample.extra == kwargs['extra']

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

        # Create a survey
        survey_kwargs = dict(zip(SURVEY_COLUMNS, SURVEYS[0]))
        survey_mod_kwargs = dict_without(survey_kwargs, 'id')
        survey = dataset.surveys.create(**survey_mod_kwargs)

        with pytest.raises(TypeError) as excinfo:
            survey.samples.get_by_id(id)

    def test_non_existant(self, empty_db):
        db = empty_db

        # Create a dataset
        dataset_kwargs = dict(zip(DATASET_COLUMNS, DATASETS[0]))
        dataset_mod_kwargs = dict_without(dataset_kwargs, 'id')
        dataset = db.datasets.create(**dataset_mod_kwargs)

        # Create a survey
        survey_kwargs = dict(zip(SURVEY_COLUMNS, SURVEYS[0]))
        survey_mod_kwargs = dict_without(survey_kwargs, 'id')
        survey = dataset.surveys.create(**survey_mod_kwargs)

        sample = survey.samples.get_by_id(99)

        assert sample is None


class TestIter:
    def test_with_no_samples(self, empty_db):
        db = empty_db

        # Create a dataset
        dataset_kwargs = dict(zip(DATASET_COLUMNS, DATASETS[0]))
        dataset_mod_kwargs = dict_without(dataset_kwargs, 'id')
        dataset = db.datasets.create(**dataset_mod_kwargs)

        # Create a survey
        survey_kwargs = dict(zip(SURVEY_COLUMNS, SURVEYS[0]))
        survey_mod_kwargs = dict_without(survey_kwargs, 'id')
        survey = dataset.surveys.create(**survey_mod_kwargs)

        samples = list(survey.samples)

        expected_samples = list()
        assert samples == expected_samples

    def test_with_populated_db(self, populated_db):
        db = populated_db

        dataset = db.datasets.get_by_id(1)
        survey = dataset.surveys.get_by_id(1)

        samples = list(survey.samples)

        for idx, sample in enumerate(samples):
            kwargs = dict(zip(SAMPLE_COLUMNS, SAMPLES[idx]))

            assert sample.id == kwargs['id']
            assert sample.survey_id == kwargs['survey_id']
            assert sample.station == kwargs['station']
            assert sample.earthmat == kwargs['earthmat']
            assert sample.name == kwargs['name']
            assert sample.lat_nad27 == kwargs['lat_nad27']
            assert sample.long_nad27 == kwargs['long_nad27']
            assert sample.lat_nad83 == kwargs['lat_nad83']
            assert sample.long_nad83 == kwargs['long_nad83']
            assert sample.x_nad27 == kwargs['x_nad27']
            assert sample.y_nad27 == kwargs['y_nad27']
            assert sample.x_nad83 == kwargs['x_nad83']
            assert sample.y_nad83 == kwargs['y_nad83']
            assert sample.zone == kwargs['zone']
            assert sample.earthmat_type == kwargs['earthmat_type']
            assert sample.status == kwargs['status']
            assert sample.extra == kwargs['extra']
