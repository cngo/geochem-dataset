import sys

__app_name__ = "Geochemistry Dataset Excel"
__app_author__ = "Canada-Nunavut Geoscience Office"

from importlib.metadata import PackageNotFoundError, version  # pragma: no cover

try:
    __app_version__ = version('geochem-dataset-excel')
except PackageNotFoundError:  # pragma: no cover
    __app_version__ = "unknown"
finally:
    del version, PackageNotFoundError


# Make the class available at package root
from .dataset import Dataset
