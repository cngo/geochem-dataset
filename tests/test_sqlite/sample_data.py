from decimal import Decimal

DATASET_COLUMNS = ('id', 'name', 'extra')
DATASETS = [
    (1, 'ca.cngo.test1', {'cat': 'Duchess'}),
]

DOCUMENT_COLUMNS = ('id', 'dataset_id', 'recommended_citation', 'extra')
DOCUMENTS = [
    (1, 1, 'test citation 1', {'cat': 'Duchess'}),
]

SURVEY_COLUMNS = ('id', 'dataset_id', 'title', 'organization', 'year_begin', 'year_end', 'party_leader', 'description', 'gsc_catalog_number', 'extra')
SURVEYS = [
    (1, 1, 'Hall Peninsula', 'CNGO', 2012, 2014, 'Duchess', 'A grand survey.', 1988, {'cat': 'Skittles'})
]

SAMPLE_COLUMNS = ('id', 'survey_id', 'station', 'earthmat', 'name', 'lat_nad27', 'long_nad27', 'lat_nad83', 'long_nad83', 'x_nad27', 'y_nad27', 'x_nad83', 'y_nad83', 'zone', 'earthmat_type', 'status', 'extra')
SAMPLES = [
    (1, 1, 'test station', 'test earthmat', 'test sample 1', Decimal(22.0), Decimal(56.0), Decimal(22.0), Decimal(56.0), Decimal(1.0), Decimal(50.0), Decimal(1.0), Decimal(50.0), 'test zone', 'test earthmat type', 'test status', {'cat': 'Skittles'}),
]

SUBSAMPLE_COLUMNS = ('id', 'sample_id', 'parent_id', 'name')
SUBSAMPLES = [
    (1, 1, None, 'test subsample 1'),
    (2, 1, 1, 'test sub-subsample 1.1'),
]

METADATA_SET_COLUMNS = ('id', 'dataset_id')
METADATA_SETS = [
    (1, 1)
]

METADATA_TYPE_COLUMNS = ('id', 'name')
METADATA_TYPES = [
    (1, 'test metadata type 1'),
]

METADATA_COLUMNS = ('id', 'metadata_set_id', 'metadata_type_id', 'value')
METADATA = [
    (1, 1, 1, 'test metadata value 1'),
]

RESULT_TYPE_COLUMNS = ('id', 'name')
RESULT_TYPES = [
    (1, 'test result type 1'),
]

RESULT_COLUMNS = ('id', 'subsample_id', 'result_type_id', 'metadata_set_id', 'value')
RESULTS = [
    (1, 2, 1, 1, 'test result 1')
]
