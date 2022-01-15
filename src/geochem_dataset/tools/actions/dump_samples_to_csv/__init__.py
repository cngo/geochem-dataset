import os
from pathlib import Path

from geochem_dataset.excel import Dataset
import pandas as pd

from .. import BaseAction, ConfigOption

CSV_COLUMNS = ('DATASET', 'DOCUMENT_RECOMMENDED_CITATION', 'SURVEY_TITLE', 'STATION', 'EARTHMAT', 'SAMPLE', 'LAT_NAD27', 'LONG_NAD27', 'LAT_NAD83', 'LONG_NAD83', 'X_NAD27', 'Y_NAD27', 'X_NAD83', 'Y_NAD83', 'ZONE', 'EARTHMAT_TYPE', 'STATUS', 'EXTRA')


class Action(BaseAction):
    NAME = "Dump samples to CSV"
    CONFIG = [
        ConfigOption('csv_path', 'CSV path', str),
    ]

    def run(self):
        self._delete_file()
        self._write_header()
        self._write_samples()
        self._done()

    def _delete_file(self):
        print(f'Deleting file {self._config["action"]["csv_path"]}...')

        try:
            Path(self._config['action']['csv_path']).unlink(missing_ok=True)
        except Exception as e:
            print(e)
            print()
            self._stop()

        print()

    def _write_header(self):
        print(f'Writing header...')

        try:
            df = pd.DataFrame(columns=CSV_COLUMNS)
            df.to_csv(self._config['action']['csv_path'], mode='w', header=True, index=False, encoding='utf-8-sig')
        except PermissionError as e:
            print(e)
            print()

            self._stop()

            return

        print()

    def _write_samples(self):
        print('Writing samples...')

        extra_columns_ok = self._config['main']['extra_columns_ok']

        for dataset_path in self._iter_dataset_paths():
            self._stop_if_requested()

            print(f'Appending samples from dataset {dataset_path.name}...', end=' ')

            try:
                with Dataset(dataset_path, extra_columns_ok=extra_columns_ok) as dataset:
                    document = list(dataset.documents)[0]

                    df = pd.DataFrame(columns=CSV_COLUMNS)
                    df = df.append([
                        {
                            'DATASET': dataset.name,
                            'DOCUMENT_RECOMMENDED_CITATION': document.recommended_citation,
                            'SURVEY_TITLE': sample.survey.title,
                            'STATION': sample.station,
                            'EARTHMAT': sample.earthmat,
                            'SAMPLE': sample.name,
                            'LAT_NAD27': sample.lat_nad27,
                            'LONG_NAD27': sample.long_nad27,
                            'LAT_NAD83': sample.lat_nad83,
                            'LONG_NAD83': sample.long_nad83,
                            'X_NAD27': sample.x_nad27,
                            'Y_NAD27': sample.y_nad27,
                            'X_NAD83': sample.x_nad83,
                            'Y_NAD83': sample.y_nad83,
                            'ZONE': sample.zone,
                            'EARTHMAT_TYPE': sample.earthmat_type,
                            'STATUS': sample.status,
                            'EXTRA': sample.extra,
                        }
                        for sample in dataset.samples
                    ])

                    try:
                        df.to_csv(self._config['action']['csv_path'], mode='a', header=False, index=False, encoding='utf-8-sig')
                    except Exception as e:
                        print(e)
                        self._stop()

            except Exception as e:
                print('FAILURE')
                print(e)
                print()
            else:
                print('SUCCESS')

        print()
