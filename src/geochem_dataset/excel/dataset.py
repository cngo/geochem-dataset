from pathlib import Path
import re

from . import errors, interfaces

DATASET_NAME_PATTERN = r'^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]$'


class Dataset:
    def __init__(self, path, *, extra_columns_ok=False):
        self.path             = Path(path)
        self.extra_columns_ok = extra_columns_ok

        if not self.path.is_dir():
            raise NotADirectoryError(self.path)

        if not re.match(DATASET_NAME_PATTERN, self.path.name):
            raise errors.InvalidDatasetNameError('Dataset name must use reverse domain name notation')

    @property
    def name(self):
        return self.path.name

    def __enter__(self):
        self.attach_interfaces()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.detach_interfaces()

    def attach_interfaces(self):
        self.documents = interfaces.DocumentsInterface(self)
        self.surveys   = interfaces.SurveysInterface(self)
        self.samples   = interfaces.SamplesInterface(self)

        try:
            self.bulk = interfaces.BulkInterface(self)
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
