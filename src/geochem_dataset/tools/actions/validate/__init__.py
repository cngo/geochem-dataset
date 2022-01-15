from geochem_dataset.excel import Dataset

from .. import BaseAction


class Action(BaseAction):
    NAME = "Validate"
    CONFIG = dict()

    def run(self):
        extra_columns_ok = self._config['main']['extra_columns_ok']

        for dataset_path in self._iter_dataset_paths():
            self._stop_if_requested()

            print(f'Validating dataset "{dataset_path.name}"...', end=' ')

            try:
                with Dataset(dataset_path, extra_columns_ok=extra_columns_ok) as dataset:
                    pass
            except Exception as e:
                print('INVALID')
                print(e)
                print()
            else:
                print('VALID')

        self._done()
