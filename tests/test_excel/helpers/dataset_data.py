from __future__ import annotations
from abc import ABC

from dataclasses import dataclass, field
from pathlib import Path

from geochem_dataset.excel.dataclasses import Result
import pandas as pd


@dataclass
class DatasetData:
    workbooks: dict[str, WorkbookData] = field(default_factory=dict)

    def to_excel(self, dataset_path: Path):
        self.workbooks['documents'].to_excel(dataset_path)
        self.workbooks['surveys'].to_excel(dataset_path)
        self.workbooks['samples'].to_excel(dataset_path)
        self.workbooks['bulk'].to_excel(dataset_path)

    @classmethod
    def from_dict(cls, dataset_data_dict: dict) -> DatasetData:
        dataset_data = cls()

        dataset_data.workbooks['documents'] = DocumentsWorkbookData.from_dict(dataset_data_dict['documents'])
        dataset_data.workbooks['surveys'] = SurveysWorkbookData.from_dict(dataset_data_dict['surveys'])
        dataset_data.workbooks['samples'] = SamplesWorkbookData.from_dict(dataset_data_dict['samples'])
        dataset_data.workbooks['bulk'] = BulkWorkbookData.from_dict(dataset_data_dict['bulk'])

        return dataset_data


@dataclass
class WorkbookData(ABC):
    worksheets: dict[str, WorksheetData] = field(default_factory=dict)

    def to_excel(self, dataset_path: Path):
        wb_path = dataset_path / self.Meta.file_name

        with pd.ExcelWriter(wb_path) as writer:
            for ws_name, ws_data in self.worksheets.items():
                df = ws_data.to_dataframe()
                df.to_excel(writer, sheet_name=ws_name, index=False, header=False)

    @classmethod
    def from_dict(cls, wb_data_dict: dict) -> WorkbookData:
        wb_data = cls()

        ws_data_class = globals()[cls.Meta.worksheet_data_class_name]

        for ws_name, ws_data_dict in wb_data_dict.items():
            wb_data.worksheets[ws_name] = ws_data_class(ws_data_dict)

        return wb_data


class DocumentsWorkbookData(WorkbookData):
    class Meta:
        file_name = 'DOCUMENT.xlsx'
        worksheet_data_class_name = 'DocumentsWorksheetData'


class SurveysWorkbookData(WorkbookData):
    class Meta:
        file_name = 'SURVEYS.xlsx'
        worksheet_data_class_name = 'SurveysWorksheetData'


class SamplesWorkbookData(WorkbookData):
    class Meta:
        file_name = 'SAMPLES.xlsx'
        worksheet_data_class_name = 'SamplesWorksheetData'


class BulkWorkbookData(WorkbookData):
    @property
    def expected_results(self):
        for ws_data in self.worksheets.values():
            for result in ws_data.expected_results:
                yield result

    def clear_subsamples(self):
        for ws_data in self.worksheets.values():
            ws_data.clear_subsamples()

    def clear_metadata_types(self):
        for ws_data in self.worksheets.values():
            ws_data.clear_metadata_types()

    def clear_result_types(self):
        for ws_data in self.worksheets.values():
            ws_data.clear_result_types()

    class Meta:
        file_name = 'BULK.xlsx'
        worksheet_data_class_name = 'AnalysisWorksheetData'


@dataclass
class WorksheetData(ABC):
    data: dict


class BasicWorksheetData(WorksheetData):
    def to_dataframe(self) -> pd.DataFrame:
        df = pd.DataFrame()

        df = df.append(pd.Series(self.Meta.headings), ignore_index=True)

        for row in self.data[self.Meta.rows_key_name]:
            row = pd.Series(row)
            df = df.append(row, ignore_index=True)

        return df

    class Meta:
        headings = None
        rows_key_name = None


class DocumentsWorksheetData(BasicWorksheetData):
    class Meta:
        headings = (
            'RECOMMENDED_CITATION',
        )
        rows_key_name = 'documents'


class SurveysWorksheetData(BasicWorksheetData):
    class Meta:
        headings = (
            'TITLE',
            'ORGANIZATION',
            'YEAR_BEGIN',
            'YEAR_END',
            'PARTY_LEADER',
            'DESCRIPTION',
            'GSC_CATALOG_NUMBER',
        )
        rows_key_name = 'surveys'


class SamplesWorksheetData(BasicWorksheetData):
    class Meta:
        headings = (
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
        rows_key_name = 'samples'


class AnalysisWorksheetData(WorksheetData):
    def to_dataframe(self) -> pd.DataFrame:
        df = pd.DataFrame()

        # Headings/result types row

        num_subsample_columns = (
            len(self.data['subsample_results_sets'][0][0])
            if self.data['subsample_results_sets']
            else 2
        )

        row = tuple((x * 'SUB' + 'SAMPLE') for x in range(num_subsample_columns))

        row += ('METADATA_TYPE',)
        row += tuple(result_type for result_type, _ in self.data['result_type_metadata_sets'])

        df = df.append(pd.Series(row), ignore_index=True)

        # Metadata rows

        num_subsample_columns = (
            len(self.data['subsample_results_sets'][0][0])
            if self.data['subsample_results_sets']
            else 2
        )

        for metadata_type_idx, metadata_type in enumerate(self.data['metadata_types']):
            row = ('',) * num_subsample_columns
            row += (metadata_type,)
            row += tuple(
                metadata[metadata_type_idx]
                for _, metadata in self.data['result_type_metadata_sets']
            )

            df = df.append(pd.Series(row), ignore_index=True)

        # Subsample/result rows

        for subsample, results in self.data['subsample_results_sets']:
            row = subsample + ('',) + results
            df = df.append(pd.Series(row), ignore_index=True)

        return df

    @property
    def expected_results(self):
        metadata_types = self.data['metadata_types']

        for subsample, results in self.data['subsample_results_sets']:
            for column_idx, result in enumerate(results):
                result_type, metadata = self.data['result_type_metadata_sets'][column_idx]

                metadata = frozenset(
                    (metadata_type, metadata_value)
                    for metadata_type, metadata_value in zip(metadata_types, metadata)
                    if metadata_value
                )

                yield Result(subsample, result_type, metadata, result)

    def clear_subsamples(self):
        self.data['subsample_results_sets'] = list()

    def clear_metadata_types(self):
        self.data['metadata_types'] = tuple()
        self.data['result_type_metadata_sets'] = [
            (result_type, tuple())
            for result_type, _ in self.data['result_type_metadata_sets']
        ]

    def clear_result_types(self):
        self.data['result_type_metadata_sets'] = list()
        self.data['subsample_results_sets'] = [
            (sample, subsample, tuple())
            for sample, subsample, _ in self.data['subsample_results_sets']
        ]
