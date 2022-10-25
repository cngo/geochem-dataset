from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from openpyxl.utils.cell import column_index_from_string, coordinate_from_string
import pandas as pd

from tests.test_excel.helpers.dataset_data.worksheet_data import WorksheetData


@dataclass
class WorkbookData:
    worksheets: dict[str, WorksheetData] = field(default_factory=dict)

    def to_excel(self, wb_path: Path, wb_mutations: dict = dict()):
        with pd.ExcelWriter(wb_path) as writer:
            for ws_name, ws_data in self.worksheets.items():
                df = ws_data.to_dataframe()

                mutations = wb_mutations.get(ws_name, dict())
                self.apply_mutations_to_dataframe(df, mutations)

                df.to_excel(writer, sheet_name=ws_name, index=False, header=False)

    @staticmethod
    def apply_mutations_to_dataframe(df: pd.DataFrame, mutations: dict[str, str]):
        for cell, value in mutations.items():
            column_xl_letter, row_xl_idx = coordinate_from_string(cell)
            column_xl_idx = column_index_from_string(column_xl_letter)

            row_idx = row_xl_idx - 1
            column_idx = column_xl_idx - 1

            df.iloc[row_idx, column_idx] = value

    @classmethod
    def from_dict(cls, wb_data_dict: dict, ws_data_class: WorksheetData) -> WorkbookData:
        worksheets = {}

        for ws_name, ws_data_dict in wb_data_dict.items():
            worksheets[ws_name] = ws_data_class(ws_data_dict)

        return cls(worksheets)
