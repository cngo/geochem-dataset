from ..dataclasses import Document
from . import SimpleExcelWorkbookInterface


class Interface(SimpleExcelWorkbookInterface):
    _name = 'DOCUMENT.xlsx'
    _sheet_name = 'DOCUMENT'
    _columns = (
        'RECOMMENDED_CITATION',
    )
    _unique_constraints = [
        ('RECOMMENDED_CITATION',)
    ]
    _foreign_key_constraints = []
    _min_count = 1
    _max_count = 1
    _dataclass = Document
    _dataclass_indexes = [
        ('recommended_citation',)
    ]

    def get_by_recommended_citation(self, recommended_citation):
        return self.get_by(recommended_citation=recommended_citation)
