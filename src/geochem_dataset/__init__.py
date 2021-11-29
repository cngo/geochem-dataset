import sys

__app_name__ = "Geochemistry Dataset"
__app_author__ = "Canada-Nunavut Geoscience Office"

from importlib.metadata import PackageNotFoundError, version  # pragma: no cover

try:
    __app_version__ = version('geochem-dataset')
except PackageNotFoundError:  # pragma: no cover
    __app_version__ = "unknown"
finally:
    del version, PackageNotFoundError
