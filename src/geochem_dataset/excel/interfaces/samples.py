from geochem_dataset.excel.dataclasses import Sample
from .bases.simple import SimpleExcelWorkbookInterface


class Interface(SimpleExcelWorkbookInterface):
    _name = 'SAMPLES.xlsx'
    _sheet_name = 'SAMPLES'
    _columns = (
        'SURVEY_TITLE',
        'STATION',
        'EARTHMAT',
        'SAMPLE',
        'LAT_NAD27',
        'LONG_NAD27',
        'LAT_NAD83',
        'LONG_NAD83',
        'X_NAD27',
        'Y_NAD27',
        'X_NAD83',
        'Y_NAD83',
        'ZONE',
        'EARTHMAT_TYPE',
        'STATUS',
    )
    _unique_constraints = [
        ('SURVEY_TITLE', 'STATION', 'EARTHMAT', 'SAMPLE'),
    ]
    _foreign_key_constraints = [
        # column, fk_interface.fk_dataclass_field
        ('SURVEY_TITLE', 'surveys.title'),
    ]
    _min_count = 1
    _max_count = None
    _dataclass = Sample
    _dataclass_indexes = [
        ('name',)
    ]
    _column_dataclass_field_map = [
        ('SAMPLE', 'name')
    ]

    def get_by_name(self, name):
        return self.get_by(name=name)
