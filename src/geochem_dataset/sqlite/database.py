from pathlib import Path

from playhouse.sqlite_ext import SqliteExtDatabase

from .. import __app_version__
from . import interfaces
from . import models


class DatasetsDatabase:
    def __init__(self, path):
        self._path = Path(path)

        if self._path.is_dir():
            raise IsADirectoryError(self._path)

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def open(self):
        do_init = not self._path.exists()

        self._db = SqliteExtDatabase(self._path, pragmas=(
            ('cache_size', -1024 * 64),
            ('journal_mode', 'wal'),
            ('foreign_keys', 1)
        ))
        models.database_proxy.initialize(self._db)

        if do_init:
            self._init()
        else:
            pass  # self._validate()

        self._attach_interfaces()

    def close(self):
        self._detach_interfaces()
        self._db.close()

    def _init(self):
        self._db.create_tables([
            models.Config,
            models.Dataset,
            models.Document,
            models.Survey,
            models.Sample,
            models.Subsample,
            models.MetadataSet,
            models.MetadataType,
            models.Metadata,
            models.ResultType,
            models.Result
        ])

        models.Config.create(name='version', value=__app_version__)

    # def _validate(self):
    #     self._validate_schema()

    # def _validate_schema(self):
    #     with tempfile.TemporaryDirectory() as tmp_dir:
    #         expected_db_path = Path(tmp_dir) / 'empty.db'

    #         with DatasetsDB(expected_db_path) as expected_db:
    #             expected_db_schema = expected_db._get_schema()

    #     if self._get_schema() != expected_db_schema:
    #         raise exceptions.InvalidDatasetsDB()

    # def _get_schema(self):
    #     cur = self._con.cursor()
    #     cur.execute('''
    #         SELECT sql FROM sqlite_master
    #          WHERE type IN ('table', 'view')
    #          ORDER BY 1;
    #     ''')
    #     schema = '\n'.join(x['sql'] for x in cur)
    #     cur.close()
    #     return schema

    def _attach_interfaces(self):
        self.config = interfaces.Config()
        self.datasets = interfaces.Datasets()

    def _detach_interfaces(self):
        del self.config
        del self.datasets



    @property
    def path(self):
        return self._path
