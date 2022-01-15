import pytest

from geochem_dataset import __app_version__
from geochem_dataset.sqlite import DatasetsDatabase


def test_new_db(db_path):
    with DatasetsDatabase(db_path) as db:
        assert db.path == db_path
        assert db.config.get_by_name('version').value == __app_version__


def test_db_with_directory(tmp_path):
    with pytest.raises(IsADirectoryError) as excinfo:
        with DatasetsDatabase(tmp_path) as db:
            pass


# def test_broken_db(initialized_db_path):
#     # Damage the DB
#     os.truncate(initialized_db_path, 50)

#     with pytest.raises(sqlite3.DatabaseError) as excinfo:
#         with DatasetsDatabase(initialized_db_path) as db:
#             pass


# def test_db_with_no_tables(db_path):
#     sqlite3.connect(db_path).close()

#     with pytest.raises(InvalidDatasetsDatabase) as excinfo:
#         with DatasetsDatabase(db_path) as db:
#             pass


# def test_db_with_missing_config_table(initialized_db_path):
#     con = sqlite3.connect(initialized_db_path)
#     cur = con.cursor()
#     cur.execute("DROP TABLE config;")
#     con.close()

#     with pytest.raises(InvalidDatasetsDatabase) as excinfo:
#         with DatasetsDatabase(initialized_db_path) as db:
#             pass


# def test_db_with_extra_tables(initialized_db_path):
#     con = sqlite3.connect(initialized_db_path)
#     cur = con.cursor()
#     cur.execute("CREATE TABLE cats (name);")
#     con.close()

#     with pytest.raises(InvalidDatasetsDatabase) as excinfo:
#         with DatasetsDatabase(initialized_db_path) as db:
#             pass


# def test_dataset_with_db_missing_table_columns(initialized_db_path):
#     con = sqlite3.connect(initialized_db_path)
#     cur = con.cursor()
#     cur.execute('ALTER TABLE config DROP COLUMN value;')
#     cur.close()
#     con.close()

#     with pytest.raises(InvalidDatasetsDatabase) as excinfo:
#         with DatasetsDatabase(initialized_db_path) as db:
#             pass
