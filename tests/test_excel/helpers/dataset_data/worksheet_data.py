from abc import ABC
from dataclasses import dataclass

import pandas as pd

from geochem_dataset.excel.dataclasses import Result


@dataclass
class WorksheetData(ABC):
    data: dict


class BasicWorksheetData(WorksheetData):
    def to_dataframe(self) -> pd.DataFrame:
        df = pd.DataFrame()

        df = df.concat(pd.Series(self.Meta.headings), ignore_index=True)

        for row in self.data[self.Meta.rows_key_name]:
            row = pd.Series(row)
            df = df.concat(row, ignore_index=True)

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

        df = df.concat(pd.Series(row), ignore_index=True)

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

            df = df.concat(pd.Series(row), ignore_index=True)

        # Subsample/result rows

        for subsample, results in self.data['subsample_results_sets']:
            row = subsample + ('',) + results
            df = df.concat(pd.Series(row), ignore_index=True)

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
