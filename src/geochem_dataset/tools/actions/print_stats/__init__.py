from geochem_dataset.excel import Dataset

from .. import BaseAction


class Action(BaseAction):
    NAME = "Print stats"
    CONFIG = dict()

    def run(self):
        extra_columns_ok = self._config['main']['extra_columns_ok']

        for dataset_path in self._iter_dataset_paths():
            self._stop_if_requested()

            print(f'Dataset: {dataset_path.name}')

            try:
                with Dataset(dataset_path, extra_columns_ok=extra_columns_ok) as dataset:
                    documents = list(dataset.documents)
                    surveys = list(dataset.surveys)
                    samples = list(dataset.samples)
                    analysis_bulk_results = list(dataset.analysis_bulk_results) if hasattr(dataset, 'analysis_bulk_results') else []

                    print("# of documents:",             len(documents))
                    print("# of surveys:",               len(surveys))
                    print("# of samples:",               len(samples))
                    print("# of analysis bulk results:", len(analysis_bulk_results))
            except Exception as e:
                print(e)
            finally:
                print()

        self._done()
