import pytest

from tests.helpers.utils import (
    set_mods,
    modified_dict, dict_without
)

from .sample_data import (
    DATASET_COLUMNS, DATASETS,
    SURVEY_COLUMNS, SURVEYS,
    SAMPLE_COLUMNS, SAMPLES,
)


class TestCreateRoot:
    def test_valid(self, empty_db):
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
        sample_mod_kwargs = dict_without(sample_kwargs, 'id')
        sample = survey.samples.create(**sample_mod_kwargs)

        # Create a root subsample (id=1)
        subsample_kwargs = dict(name="subsample-1")
        subsample = sample.subsamples.create(**subsample_kwargs)

        assert subsample.id == 1
        assert subsample.sample == sample
        assert subsample.sample_id == sample.id
        assert subsample.parent == None
        assert subsample.parent_id == None
        assert subsample.name == subsample_kwargs['name']

    INVALID_FIELD_DATA = {
        'id__given'       : (set_mods('id', value=99), ValueError),
        'sample_id__given': (set_mods('sample_id', value=99), ValueError),
        'parent_id__given': (set_mods('parent_id', value=99), ValueError),
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
        sample_mod_kwargs = dict_without(sample_kwargs, 'id')
        sample = survey.samples.create(**sample_mod_kwargs)

        # Attempt to create a root subsample with modifications
        with pytest.raises(expected_exc):
            subsample_kwargs = dict(name="subsample-1")
            subsample_mod_kwargs = modified_dict(subsample_kwargs, mods)
            sample.subsamples.create(**subsample_mod_kwargs)


class TestCreateChild:
    def test_valid(self, empty_db):
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
        sample_mod_kwargs = dict_without(sample_kwargs, 'id')
        sample = survey.samples.create(**sample_mod_kwargs)

        # Create a root subsample (id=1)
        root_subsample_kwargs = dict(name="root-subsample")
        root_subsample = sample.subsamples.create(**root_subsample_kwargs)

        # Create a child subsample (id=2)
        child_subsample_kwargs = {
            'name': "child-subsample"
        }
        child_subsample = root_subsample.children.create(**child_subsample_kwargs)

        assert child_subsample.id == 2
        assert child_subsample.sample == sample
        assert child_subsample.parent == root_subsample
        assert child_subsample.name == child_subsample_kwargs['name']

    INVALID_FIELD_DATA = {
        'id__given'       : (set_mods('id', value=99), ValueError),
        'sample_id__given': (set_mods('sample_id', value=99), ValueError),
        'parent_id__given': (set_mods('parent_id', value=99), ValueError),
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
        sample_mod_kwargs = dict_without(sample_kwargs, 'id')
        sample = survey.samples.create(**sample_mod_kwargs)

        # Create a root subsample (id=1)
        root_subsample_kwargs = dict(name="root-subsample")
        root_subsample = sample.subsamples.create(**root_subsample_kwargs)

        # Attempt to create a child subsample
        with pytest.raises(expected_exc):
            child_subsample_kwargs = dict(name="child-subsample")
            child_subsample_mod_kwargs = modified_dict(child_subsample_kwargs, mods)
            root_subsample.children.create(**child_subsample_mod_kwargs)


# class TestGetByID:
#     @pytest.mark.parametrize('kwargs', [dict(zip(SAMPLE_COLUMNS, x)) for x in SAMPLES])
#     def test_valid(self, populated_db, kwargs):
#         dataset = populated_db.datasets.get_by_id(1)
#         survey = dataset.surveys.get_by_id(kwargs['survey_id'])
#         sample = survey.samples.get_by_id(kwargs['id'])

#         assert sample.id == kwargs['id']
#         assert sample.survey_id == kwargs['survey_id']
#         assert sample.station == kwargs['station']
#         assert sample.earthmat == kwargs['earthmat']
#         assert sample.name == kwargs['name']
#         assert sample.lat_nad27 == kwargs['lat_nad27']
#         assert sample.long_nad27 == kwargs['long_nad27']
#         assert sample.lat_nad83 == kwargs['lat_nad83']
#         assert sample.long_nad83 == kwargs['long_nad83']
#         assert sample.x_nad27 == kwargs['x_nad27']
#         assert sample.y_nad27 == kwargs['y_nad27']
#         assert sample.x_nad83 == kwargs['x_nad83']
#         assert sample.y_nad83 == kwargs['y_nad83']
#         assert sample.zone == kwargs['zone']
#         assert sample.earthmat_type == kwargs['earthmat_type']
#         assert sample.status == kwargs['status']
#         assert sample.extra == kwargs['extra']

#     INVALID_ID_DATA = {
#         'wrong_type__str':      ('Skittles',),
#         'wrong_type__NoneType': (None,),
#         'wrong_type__dict':     ({'cat': 'Skittles'},),
#     }

#     @pytest.mark.parametrize('id', list(INVALID_ID_DATA.values()), ids=list(INVALID_ID_DATA.keys()))
#     def test_invalid(self, empty_db, id):
#         db = empty_db

#         # Create a dataset
#         dataset_kwargs = dict(zip(DATASET_COLUMNS, DATASETS[0]))
#         dataset_mod_kwargs = dict_without(dataset_kwargs, 'id')
#         dataset = db.datasets.create(**dataset_mod_kwargs)

#         # Create a survey
#         survey_kwargs = dict(zip(SURVEY_COLUMNS, SURVEYS[0]))
#         survey_mod_kwargs = dict_without(survey_kwargs, 'id')
#         survey = dataset.surveys.create(**survey_mod_kwargs)

#         with pytest.raises(TypeError) as excinfo:
#             survey.samples.get_by_id(id)

#     def test_non_existant(self, empty_db):
#         db = empty_db

#         # Create a dataset
#         dataset_kwargs = dict(zip(DATASET_COLUMNS, DATASETS[0]))
#         dataset_mod_kwargs = dict_without(dataset_kwargs, 'id')
#         dataset = db.datasets.create(**dataset_mod_kwargs)

#         # Create a survey
#         survey_kwargs = dict(zip(SURVEY_COLUMNS, SURVEYS[0]))
#         survey_mod_kwargs = dict_without(survey_kwargs, 'id')
#         survey = dataset.surveys.create(**survey_mod_kwargs)

#         sample = survey.samples.get_by_id(99)

#         assert sample is None


# class TestIter:
#     def test_with_no_samples(self, empty_db):
#         db = empty_db

#         # Create a dataset
#         dataset_kwargs = dict(zip(DATASET_COLUMNS, DATASETS[0]))
#         dataset_mod_kwargs = dict_without(dataset_kwargs, 'id')
#         dataset = db.datasets.create(**dataset_mod_kwargs)

#         # Create a survey
#         survey_kwargs = dict(zip(SURVEY_COLUMNS, SURVEYS[0]))
#         survey_mod_kwargs = dict_without(survey_kwargs, 'id')
#         survey = dataset.surveys.create(**survey_mod_kwargs)

#         samples = list(survey.samples)

#         expected_samples = list()
#         assert samples == expected_samples

#     def test_with_populated_db(self, populated_db):
#         dataset = populated_db.datasets.get_by_id(1)
#         survey = dataset.surveys.get_by_id(1)

#         samples = list(survey.samples)

#         for idx, sample in enumerate(samples):
#             kwargs = dict(zip(SAMPLE_COLUMNS, SAMPLES[idx]))

#             assert sample.id == kwargs['id']
#             assert sample.survey_id == kwargs['survey_id']
#             assert sample.station == kwargs['station']
#             assert sample.earthmat == kwargs['earthmat']
#             assert sample.name == kwargs['name']
#             assert sample.lat_nad27 == kwargs['lat_nad27']
#             assert sample.long_nad27 == kwargs['long_nad27']
#             assert sample.lat_nad83 == kwargs['lat_nad83']
#             assert sample.long_nad83 == kwargs['long_nad83']
#             assert sample.x_nad27 == kwargs['x_nad27']
#             assert sample.y_nad27 == kwargs['y_nad27']
#             assert sample.x_nad83 == kwargs['x_nad83']
#             assert sample.y_nad83 == kwargs['y_nad83']
#             assert sample.zone == kwargs['zone']
#             assert sample.earthmat_type == kwargs['earthmat_type']
#             assert sample.status == kwargs['status']
#             assert sample.extra == kwargs['extra']
