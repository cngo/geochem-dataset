from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from tests.test_excel.helpers.dataset_data.workbook_data import WorkbookData
from tests.test_excel.helpers.dataset_data.worksheet_data import (
    DocumentsWorksheetData,
    SurveysWorksheetData,
    SamplesWorksheetData,
    AnalysisWorksheetData,
)

WS_DATA_CLASS_MAP = {
    'DOCUMENT.xlsx': DocumentsWorksheetData,
    'SURVEYS.xlsx': SurveysWorksheetData,
    'SAMPLES.xlsx': SamplesWorksheetData,
    'BULK.xlsx': AnalysisWorksheetData,
}


@dataclass
class DatasetData:
    workbooks: dict[str, WorkbookData] = field(default_factory=dict)

    def to_excel(self, dataset_path: Path, mutations: dict[dict[dict[str, str]]] = dict()):
        for wb_name, wb_data in self.workbooks.items():
            wb_mutations = mutations.get(wb_name, dict())
            wb_data.to_excel(dataset_path / wb_name, wb_mutations)

    @classmethod
    def from_dict(cls, dataset_data_dict: dict) -> DatasetData:
        workbooks = {}

        for wb_name, wb_data_dict in dataset_data_dict.items():
            ws_data_class = WS_DATA_CLASS_MAP[wb_name]
            workbooks[wb_name] = WorkbookData.from_dict(wb_data_dict, ws_data_class)

        return cls(workbooks)
