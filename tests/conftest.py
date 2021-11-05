import os
import shutil
import sys

import pytest


sys.path.append(os.path.join(os.path.dirname(__file__), 'helpers'))


@pytest.fixture
def dataset_path(tmp_path):
    dataset_path = tmp_path / 'ca.cngo.test'
    dataset_path.mkdir()

    shutil.copytree('./tests/datasets/ca.cngo.test', dataset_path, dirs_exist_ok=True)

    return dataset_path
