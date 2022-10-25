import json
import sqlite3

from geochem_dataset.sqlite import DatasetsDatabase
import pytest

from tests.helpers.utils import dict_without
from .sample_data import (
    DATASET_COLUMNS, DATASETS,
    DOCUMENT_COLUMNS, DOCUMENTS,
    SURVEY_COLUMNS, SURVEYS,
    SAMPLE_COLUMNS, SAMPLES,
    SUBSAMPLE_COLUMNS, SUBSAMPLES,
    METADATA_SET_COLUMNS, METADATA_SETS,
    METADATA_TYPE_COLUMNS, METADATA_TYPES,
    METADATA_COLUMNS, METADATA,
    RESULT_TYPE_COLUMNS, RESULT_TYPES,
    RESULT_COLUMNS, RESULTS
)


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / 'datasets.db'


@pytest.fixture
def empty_db_path(db_path):
    con = sqlite3.connect(db_path)
    cur = con.cursor()

    with open('tests/test_sqlite/init_db.sql') as f:
        cur.executescript(f.read())

    con.commit()
    con.close()

    return db_path


@pytest.fixture
def empty_db(empty_db_path):
    with DatasetsDatabase(empty_db_path) as db:
        yield db


@pytest.fixture
def populated_db_path(empty_db_path):
    db_path = empty_db_path

    con = sqlite3.connect(db_path)
    cur = con.cursor()

    insert_sample_data(cur, 'datasets', DATASET_COLUMNS, DATASETS)
    insert_sample_data(cur, 'documents', DOCUMENT_COLUMNS, DOCUMENTS)
    insert_sample_data(cur, 'surveys', SURVEY_COLUMNS, SURVEYS)
    insert_sample_data(cur, 'samples', SAMPLE_COLUMNS, SAMPLES)
    insert_sample_data(cur, 'subsamples', SUBSAMPLE_COLUMNS, SUBSAMPLES)
    insert_sample_data(cur, 'metadata_sets', METADATA_SET_COLUMNS, METADATA_SETS)
    insert_sample_data(cur, 'metadata_types', METADATA_TYPE_COLUMNS, METADATA_TYPES)
    insert_sample_data(cur, 'metadata', METADATA_COLUMNS, METADATA)
    insert_sample_data(cur, 'result_types', RESULT_TYPE_COLUMNS, RESULT_TYPES)
    insert_sample_data(cur, 'results', RESULT_COLUMNS, RESULTS)

    con.commit()
    con.close()

    return db_path


def insert_sample_data(cur, table, columns, rows):
    for values in rows:
        kwargs = dict(zip(columns, values))
        kwargs_without_id = dict_without(kwargs, 'id')

        if 'extra' in kwargs_without_id and isinstance(kwargs_without_id['extra'], dict):
            kwargs_without_id['extra'] = json.dumps(kwargs_without_id['extra'])

        columns_str = ', '.join([x for x in columns if x != 'id'])
        value_placeholders_str = ', '.join(f':{x}' for x in columns if x != 'id')

        cur.execute(f'INSERT INTO {table} ({columns_str}) VALUES ({value_placeholders_str});', kwargs_without_id)
        assert cur.lastrowid == kwargs['id']


@pytest.fixture
def populated_db(populated_db_path):
    with DatasetsDatabase(populated_db_path) as db:
        yield db
