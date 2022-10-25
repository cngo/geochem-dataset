from pathlib import Path

import pandas as pd
import pytest

from tests.test_excel.helpers.dataset_data import DatasetData

TEST_DATA = {
    'DOCUMENT.xlsx': {
        'DOCUMENT': {
            'documents': [
                ('A test citation',),
            ]
        }
    },
    'SURVEYS.xlsx': {
        'SURVEYS': {
            'surveys': [
                ('2011, Till sampling survey, Hall Peninsula. Canada-Nunavut Geoscience Office', 'Canada-Nunavut Geoscience Office', 2011, 2013, 'Tremblay, Tommy', 'A test description', 1000),
            ]
        }
    },
    'SAMPLES.xlsx': {
        'SAMPLES': {
            'samples': [
                ('2011, Till sampling survey, Hall Peninsula. Canada-Nunavut Geoscience Office', '11TIAT001', '11TIAT001A', '11TIAT001A01', None, None, 64.010103, -67.351092, None, None, None, None, None, 'Till', None),
                ('2011, Till sampling survey, Hall Peninsula. Canada-Nunavut Geoscience Office', '11TIAT024', '11TIAT024A', '11TIAT024A01', None, None, 64.472825, -67.721319, None, None, None, None, None, 'Till', None),
                ('2011, Till sampling survey, Hall Peninsula. Canada-Nunavut Geoscience Office', '12TIAT138', '12TIAT138A', '12TIAT138A01', None, None, 64.209300, -67.011316, None, None, None, None, None, 'Till', None),
                ('2011, Till sampling survey, Hall Peninsula. Canada-Nunavut Geoscience Office', '12TIAT139', '12TIAT139A', '12TIAT139A01', None, None, 64.334217, -67.087329, None, None, None, None, None, 'Till', None),
            ]
        }
    },
    'BULK.xlsx': {
        'BULK1': {
            'subsample_results_sets': [
                (('11TIAT001A01', '11TIAT001A01',), ('2.5Y 6/4', 'light yellowish brown', '7.256')),
                (('11TIAT024A01', '11TIAT024A01',), ('2.5Y 5/4', 'light olive brown', '22.173')),
            ],
            'metadata_types': ('Method', 'Threshold', 'Unit', 'Fraction_min', 'Fraction_max', 'Year', 'Lab_analysis'),
            'result_type_metadata_sets': [
                ('Soil_Munsell', ('SP64 Series X-Rite Spectrophotometer', '', '', '0', '2mm', '2013', 'GSC Sedimentology')),
                ('Colour_Description', ('SP64 Series X-Rite Spectrophotometer', '', '', '0', '2mm', '2013', 'GSC Sedimentology')),
                ('W_peb_bulk', ('laser particle size analyzer and Camsizer & Lecotrac LT100', '', 'pct', '0', '30cm', '2013', 'GSC Sedimentology')),
            ],
        },
        'BULK2': {
            'subsample_results_sets': [
                (('12TIAT138A01', '12TIAT138A01',), ('2.5Y 6/4', 'light yellowish brown', '12.699')),
                (('12TIAT139A01', '12TIAT139A01',), ('2.5Y 5/4', 'light olive brown', '22.173')),
            ],
            'metadata_types': ('Method', 'Threshold', 'Unit', 'Fraction_min', 'Fraction_max', 'Year', 'Lab_analysis'),
            'result_type_metadata_sets': [
                ('Soil_Munsell', ('SP64 Series X-Rite Spectrophotometer', '', '', '0', '2mm', '2013', 'GSC Sedimentology')),
                ('Colour_Description', ('SP64 Series X-Rite Spectrophotometer', '', '', '0', '2mm', '2013', 'GSC Sedimentology')),
                ('W_peb_bulk', ('laser particle size analyzer and Camsizer & Lecotrac LT100', '', 'pct', '0', '30cm', '2013', 'GSC Sedimentology')),
            ],
        }
    }
}


@pytest.fixture
def test_dataset_data() -> DatasetData:
    return DatasetData.from_dict(TEST_DATA)


@pytest.fixture
def test_dataset_path(tmp_path) -> Path:
    dataset_path = tmp_path / 'ca.cngo.test'
    dataset_path.mkdir()
    return dataset_path
