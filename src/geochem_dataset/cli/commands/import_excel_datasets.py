import os
import logging
from pathlib import Path

from tqdm import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm

from geochem_dataset.excel import Dataset as DatasetXL
from geochem_dataset.excel import errors as xl_errors
from geochem_dataset.sqlite import DatasetsDatabase as DatasetsDB
from geochem_dataset.sqlite.models import Result as DBResult


LOG = logging.getLogger(__name__)

DEBUG           = (os.getenv('DEBUG_PYTHON', 'False') == 'True')
DEBUG_LOG_LEVEL = (getattr(logging, os.getenv('DEBUG_PYTHON_LOG_LEVEL', 'DEBUG')))

logging.basicConfig(level=logging.INFO)

if DEBUG:
    import ipdb
    LOG.setLevel(DEBUG_LOG_LEVEL)


def main(db_path: Path, datasets_path: Path, *, dataset_name: str = None, replace: bool = False):
    if db_path.exists():
        if replace:
            db_path.unlink(missing_ok=True)
        else:
            raise FileExistsError

    with DatasetsDB(db_path) as db:
        for dataset_path in sorted(datasets_path.iterdir()):
            if dataset_name and dataset_path.name != dataset_name:
                continue

            assert dataset_path.is_dir()
            importer = DatasetImporter(dataset_path, db)
            importer.begin()


class DatasetImporter:
    def __init__(self, dataset_path: Path, db: DatasetsDB):
        self.dataset_path = dataset_path
        self.db = db

    def begin(self):
        print(f"Import dataset: {self.dataset_path}")

        try:
            self._excel_dataset = DatasetXL(self.dataset_path, extra_columns_ok=True)
            self._excel_dataset.attach_interfaces()

            self._insert_dataset()
            self._insert_documents()
            self._insert_surveys()
            self._insert_samples()

            if hasattr(self._excel_dataset, "bulk"):
                self._insert_bulk()
        except xl_errors.IntegrityError as e:
            logging.error(f"Excel Error: {str(e)}")

        print()

    def _insert_dataset(self):
        print(f'Insert dataset: {self._excel_dataset.name}')

        self._db_dataset = self.db.datasets.create(name=self._excel_dataset.name)

    def _insert_documents(self):
        self._db_documents = {}

        for excel_document in tqdm(self._excel_dataset.documents, total=self._excel_dataset.documents.count, desc="Insert documents"):
            db_document = self._db_dataset.documents.create(
                recommended_citation = excel_document.recommended_citation,
                extra                = excel_document.extra,
            )
            self._db_documents[db_document.recommended_citation] = db_document

        assert len(self._db_documents) == 1

    def _insert_surveys(self):
        self._db_surveys = {}

        for excel_survey in tqdm(self._excel_dataset.surveys, total=self._excel_dataset.surveys.count, desc="Insert surveys"):
            db_survey = self._db_dataset.surveys.create(
                title              = excel_survey.title,
                organization       = excel_survey.organization,
                year_begin         = excel_survey.year_begin,
                year_end           = excel_survey.year_end,
                party_leader       = excel_survey.party_leader,
                description        = excel_survey.description,
                gsc_catalog_number = excel_survey.gsc_catalog_number,
                extra              = excel_survey.extra,
            )
            self._db_surveys[db_survey.title] = db_survey

    def _insert_samples(self):
        self._db_samples = {}

        for excel_sample in tqdm(self._excel_dataset.samples, total=self._excel_dataset.samples.count, desc="Insert samples"):
            excel_survey = self._excel_dataset.surveys.get_by_row_idx(excel_sample.surveys_row_idx)
            db_survey = self._db_surveys[excel_survey.title]
            db_sample = db_survey.samples.create(
                station       = excel_sample.station,
                earthmat      = excel_sample.earthmat,
                name          = excel_sample.name,
                lat_nad27     = excel_sample.lat_nad27,
                long_nad27    = excel_sample.long_nad27,
                lat_nad83     = excel_sample.lat_nad83,
                long_nad83    = excel_sample.long_nad83,
                x_nad27       = excel_sample.x_nad27,
                y_nad27       = excel_sample.y_nad27,
                x_nad83       = excel_sample.x_nad83,
                y_nad83       = excel_sample.y_nad83,
                zone          = excel_sample.zone,
                earthmat_type = excel_sample.earthmat_type,
                status        = excel_sample.status,
                extra         = excel_sample.extra,
            )
            self._db_samples[excel_sample.name] = db_sample

    def _insert_bulk(self):
        xl_samples        = {}
        db_metadata_types = {}
        db_result_types   = {}
        db_metadata_sets  = {}
        db_subsamples     = {}

        with logging_redirect_tqdm():
            results_iter = self._excel_dataset.bulk.results
            result_count = self._excel_dataset.bulk.result_count

            results_chunk_size = 50
            results_chunk = []

            for xl_result in tqdm(results_iter, total=result_count, desc="Insert bulk results"):
                # sample
                if (xl_sample := xl_samples.get(xl_result.sample_row_idx, None)) is None:
                    xl_samples[xl_result.sample_row_idx] = \
                        self._excel_dataset.samples.get_by_row_idx(xl_result.sample_row_idx)
                    xl_sample = xl_samples[xl_result.sample_row_idx]
                db_sample = self._db_samples[xl_sample.name]

                # subsample
                if xl_result.subsample not in db_subsamples:
                    for i, subsample_part_i in enumerate(xl_result.subsample):
                        if i == 0:
                            db_subsample_i = db_sample.subsamples.get_by_name(name=subsample_part_i)
                            if db_subsample_i is None:
                                db_subsample_i = db_sample.subsamples.create(name=subsample_part_i)
                        else:
                            db_subsample_i = db_subsample.children.get_by_name(name=subsample_part_i)
                            if db_subsample_i is None:
                                db_subsample_i = db_subsample.children.create(name=subsample_part_i)
                        db_subsample = db_subsample_i
                    db_subsamples[xl_result.subsample] = db_subsample
                db_subsample = db_subsamples[xl_result.subsample]

                # result type
                if xl_result.type not in db_result_types:
                    db_result_type = self._db_dataset.result_types.create(name=xl_result.type)
                    db_result_types[xl_result.type] = db_result_type
                db_result_type = db_result_types[xl_result.type]

                # metadata set
                if xl_result.metadata_set not in db_metadata_sets:
                    db_metadata_set = self._db_dataset.metadata_sets.create()
                    db_metadata_sets[xl_result.metadata_set] = db_metadata_set
                    # metadata types and values
                    for metadata_type, metadata_value in xl_result.metadata_set:
                        # metadata type
                        if (db_metadata_type := db_metadata_types.get(metadata_type, None)) is None:
                            db_metadata_type = self._db_dataset.metadata_types.create(name=metadata_type)
                            db_metadata_types[metadata_type] = db_metadata_type
                        # metadata value
                        if metadata_value is not None:
                            db_metadata_set.items.create(metadata_type_id=db_metadata_type.id, value=metadata_value)
                db_metadata_set = db_metadata_sets[xl_result.metadata_set]

                # result
                results_chunk.append((db_subsample.id, db_result_type.id, db_metadata_set.id, xl_result.value))
                if len(results_chunk) == results_chunk_size:
                    with self.db._db.atomic():
                        DBResult.insert_many(results_chunk).execute()
                    results_chunk = []
            else:
                if results_chunk:
                    with self.db._db.atomic():
                        DBResult.insert_many(results_chunk).execute()
                    results_chunk = []
