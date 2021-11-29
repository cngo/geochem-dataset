from ..dataclasses import Survey
from . import SimpleExcelWorkbookInterface


class Interface(SimpleExcelWorkbookInterface):
    _name = 'SURVEYS.xlsx'
    _sheet_name = 'SURVEYS'
    _columns = (
        'TITLE',
        'ORGANIZATION',
        'YEAR_BEGIN',
        'YEAR_END',
        'PARTY_LEADER',
        'DESCRIPTION',
        'GSC_CATALOG_NUMBER',
    )
    _unique_constraints = [
        ('TITLE',)
    ]
    _foreign_key_constraints = []
    _min_count = 1
    _max_count = None
    _dataclass = Survey
    _dataclass_indexes = [
        ('title',)
    ]

    def get_by_title(self, title):
        return self.get_by(title=title)
