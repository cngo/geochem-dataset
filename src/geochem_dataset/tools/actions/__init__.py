from abc import ABC, abstractclassmethod
from collections import namedtuple
from importlib import import_module
from pathlib import Path
from pkgutil import iter_modules
import sys


ConfigOption = namedtuple('ConfigOption', ('name', 'nice_name', 'type'))


class BaseAction(ABC):
    NAME: str = "Nice Action Name"
    CONFIG: list['ConfigOption'] = list()

    def __init__(self, *, config, get_stop_request=None, event_triggers=None):
        self._config = config
        self._get_stop_request = get_stop_request
        self._event_triggers = event_triggers

    @abstractclassmethod
    def run(self):
        pass

    def _iter_dataset_paths(self):
        datasets_path = self._config['main']['datasets_path']
        datasets_to_process = self._config['main']['datasets_to_process']
        datasets_to_ignore = self._config['main']['datasets_to_ignore']

        for dataset_path in Path(datasets_path).iterdir():
            if not dataset_path.is_dir():
                continue

            if len(datasets_to_process) > 0 and dataset_path.name not in datasets_to_process:
                continue

            if len(datasets_to_ignore) > 0 and dataset_path.name in datasets_to_ignore:
                continue

            yield dataset_path

    def _stop_if_requested(self):
        if self._get_stop_request and self._get_stop_request():
            self._stop()

    def _stop(self):
        if self._event_triggers:
            self._event_triggers['stopped']()
            sys.exit()

    def _done(self):
        if self._event_triggers:
            self._event_triggers['done']()


# Manually create actions map
#
# from .dump_samples_to_csv import Action as DumpSamplesToCSVAction
# from .print_stats import Action as PrintStatsAction
# from .validate import Action as ValidateAction

# __actions__ = {
#     'dump_samples_to_csv': DumpSamplesToCSVAction,
#     'print_stats': PrintStatsAction,
#     'validate': ValidateAction
# }


# Automatically create actions map

def get_actions_map():
    actions = {}

    for mi in iter_modules(__path__):
        if not mi.ispkg:
            continue

        action_module = import_module(f'.{mi.name}', package=__package__)
        action_class = action_module.Action

        actions[mi.name] = action_class

    return actions

__actions__ = get_actions_map()
del get_actions_map
