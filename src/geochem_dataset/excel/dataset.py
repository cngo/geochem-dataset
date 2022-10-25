from pathlib import Path
import re

from .exceptions import InvalidDatasetNameError
from .interfaces.documents import Interface as DocumentsInterface
from .interfaces.surveys import Interface as SurveysInterface
from .interfaces.samples import Interface as SamplesInterface
from .interfaces.analysis_bulk import Interface as AnalysisBulkInterface


class Dataset:
    DATASET_NAME_PATTERN = r'^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]$'

    def __init__(self, path, *, extra_columns_ok=False):
        self._path = Path(path)
        self._extra_columns_ok = extra_columns_ok

        if not self._path.is_dir():
            raise NotADirectoryError(self._path)

        if not re.match(self.DATASET_NAME_PATTERN, self._path.name):
            raise InvalidDatasetNameError('Dataset name must use reverse domain name notation')

    @property
    def path(self):
        return self._path

    @property
    def name(self):
        return self._path.name

    @property
    def extra_columns_ok(self):
        return self._extra_columns_ok

    def __enter__(self):
        self.attach_interfaces()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.detach_interfaces()

    def attach_interfaces(self):
        self.documents = DocumentsInterface(self)
        self.surveys = SurveysInterface(self)
        self.samples = SamplesInterface(self)

        try:
            self.bulk = AnalysisBulkInterface(self)
        except FileNotFoundError:
            pass

    def detach_interfaces(self):
        delattr(self, 'documents')
        delattr(self, 'surveys')
        delattr(self, 'samples')

        try:
            delattr(self, 'bulk')
        except AttributeError:
            pass
