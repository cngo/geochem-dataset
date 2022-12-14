from __future__ import annotations

from abc import ABC
from dataclasses import asdict, dataclass, field
from pathlib import Path

from openpyxl.utils.cell import column_index_from_string, coordinate_from_string
import pandas as pd

from geochem_dataset.excel.models import \
    Document, Survey, Sample, Result, ResultSubsample, ResultMetadata

# Abbreviations:
# wb = workbook
# ws = worksheet
# mod(s) = modification(s)


@dataclass
class DatasetExcelData:
    workbooks: dict[str, WorkbookData] = field(default_factory=dict)

    def __getitem__(self, wb_name):
        return self.workbooks[wb_name]

    def to_excel(self, dataset_path: Path, mods: dict[dict[dict[str, str]]] = dict()):
        for wb_name, wb_data in self.workbooks.items():
            wb_mods = mods.get(wb_name, dict())
            wb_data.to_excel(dataset_path / wb_name, wb_mods)

    @classmethod
    def from_dict(cls, fixture_data: dict) -> DatasetExcelData:
        data = cls()

        for wb_name, wb_data_dict in fixture_data.items():
            wb_data_class = WORKBOOK_DATA_CLASSES[wb_name]
            ws_data_class = WORKSHEET_DATA_CLASSES[wb_name]
            data.workbooks[wb_name] = wb_data_class.from_dict(data, wb_data_dict, ws_data_class)

        return data


@dataclass
class WorkbookData:
    root: DatasetExcelData
    worksheets: dict[str, WorksheetData] = field(default_factory=dict)

    def __getitem__(self, ws_name):
        return self.worksheets[ws_name]

    def to_excel(self, wb_path: Path, mods: dict = dict()):
        with pd.ExcelWriter(wb_path) as writer:
            for ws_name, ws_data in self.worksheets.items():
                df = ws_data.to_dataframe()

                mods = mods.get(ws_name, dict())
                self.apply_mods_to_dataframe(df, mods)

                df.to_excel(writer, sheet_name=ws_name, index=False, header=False)

    @classmethod
    def from_dict(cls, data: DatasetExcelData, wb_data_dict: dict, ws_data_class) -> WorkbookData:
        wb_data = cls(data)

        for ws_name, ws_data_dict in wb_data_dict.items():
            wb_data.worksheets[ws_name] = ws_data_class(wb_data, ws_data_dict)

        return wb_data

    @staticmethod
    def apply_mods_to_dataframe(df: pd.DataFrame, mods: dict[str, str]):
        for cell, value in mods.items():
            column_xl_letter, row_xl_idx = coordinate_from_string(cell)
            column_xl_idx = column_index_from_string(column_xl_letter)

            row_idx = row_xl_idx - 1
            column_idx = column_xl_idx - 1

            df.iloc[row_idx, column_idx] = value


@dataclass
class BasicWorkbookData(WorkbookData):
    def iter_objects(self):
        for ws_name, ws_data in self.worksheets.items():
            for row in ws_data.iter_objects():
                yield row


@dataclass
class AnalysisWorkbookData(WorkbookData):
    def iter_objects(self):
        for ws_name, ws_data in self.worksheets.items():
            for result in ws_data.iter_objects():
                yield result


@dataclass
class WorksheetData(ABC):
    workbook_data: WorkbookData
    data: dict


class BasicWorksheetData(WorksheetData):
    def to_dataframe(self) -> pd.DataFrame:
        df = pd.DataFrame()
        df = pd.concat([df, pd.Series(self.Meta.headings).to_frame().T], ignore_index=True)

        for row in self.data[self.Meta.rows_key_name]:
            df = pd.concat([df, pd.Series(row).to_frame().T])

        return df

    def iter_objects(self):
        headings = self.Meta.headings
        extra_headings = getattr(self.Meta, 'extra_headings', tuple())

        for row in self.data[self.Meta.rows_key_name]:
            args = row[:len(headings)][0]

            if len(extra_headings):
                extra_headings_start_idx = len(extra_headings) * -1
                extra = dict(zip(extra_headings, row[extra_headings_start_idx:]))
                args += [extra]

            yield self.Meta.object_class(*args)

    class Meta:
        object         = None
        headings       = None
        extra_headings = None
        rows_key_name  = None


class DocumentsWorksheetData(BasicWorksheetData):
    class Meta:
        object_class = Document
        headings = (
            'RECOMMENDED_CITATION',
        )
        rows_key_name = 'documents'


class SurveysWorksheetData(BasicWorksheetData):
    class Meta:
        object_class = Survey
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
        object_class = Sample
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

    def iter_objects(self):
        surveys = list(self.workbook_data.dataset_excel_data.workbooks['SURVEYS.xlsx'].worksheets['SURVEYS'].iter_objects())

        for sample in super().iter_objects():
            sample_dict = asdict(sample)
            sample_dict['survey'] = [x for x in surveys if x.title == sample.survey][0]
            yield self.Meta.object_class(**sample_dict)


class AnalysisWorksheetData(WorksheetData):
    def iter_objects(self):
        metadata_types = self.data['metadata_types']

        for subsample, results in self.data['subsample_results_sets']:
            sample = subsample[0]
            subsample = tuple(subsample[1:])

            for column_idx, value in enumerate(results):
                result_type, metadata = self.data['result_type_metadata_sets'][column_idx]
                metadata = {k: v for k, v in zip(metadata_types, metadata) if v}

                yield Result(sample, subsample, result_type, metadata, value)

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

        df = pd.concat([df, pd.Series(row).to_frame().T])

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

            df = pd.concat([df, pd.Series(row).to_frame().T])

        # Subsample/result rows

        for subsample, results in self.data['subsample_results_sets']:
            row = list(subsample) + [''] + list(results)
            df = pd.concat([df, pd.Series(row).to_frame().T])

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
            (subsample, tuple())
            for subsample, _ in self.data['subsample_results_sets']
        ]


WORKBOOK_DATA_CLASSES = {
    'DOCUMENT.xlsx': BasicWorkbookData,
    'SURVEYS.xlsx' : BasicWorkbookData,
    'SAMPLES.xlsx' : BasicWorkbookData,
    'BULK.xlsx'    : AnalysisWorkbookData,
}

WORKSHEET_DATA_CLASSES = {
    'DOCUMENT.xlsx': DocumentsWorksheetData,
    'SURVEYS.xlsx' : SurveysWorksheetData,
    'SAMPLES.xlsx' : SamplesWorksheetData,
    'BULK.xlsx'    : AnalysisWorksheetData,
}
