from enum import Enum
import os
import re
import threading
from typing import Iterable

import PySimpleGUI as sg

from .. import __app_name__, __app_version__
from .actions import __actions__
from .config import config


class StdOutDest(Enum):
    TERMINAL = 1
    GUI = 2


__stdout_destination__ = StdOutDest.GUI


sg.theme('DarkAmber')


def main():
    Interface().run()


class Interface:
    __title__ = f'{__app_name__} (Version: {__app_version__})'

    _thread = None
    _stop_thread = False

    def run(self):
        self._create_window()

        while True:
            event, values = self._window.read()

            if event == sg.WIN_CLOSED or event == 'Exit':
                break

            self._handle_event(event, values)

        self._save_config(values)
        self._window.close()

    def _create_window(self):
        self._window = sg.Window(self.__title__, self._get_window_layout(), finalize=True)
        self._load_config_into_window()

    def _get_window_layout(self):
        layout = [
            [
                sg.Text('Datasets path:'),
                sg.InputText(key='main.datasets_path', metadata={'type': str}),
            ],
            [
                sg.Text('Datasets to process:'),
                sg.InputText(key='main.datasets_to_process', metadata={'type': str, 'clean': clean_comma_seperated_list}),
                sg.Text('Comma-separated values')
            ],
            [
                sg.Text('Datsets to ignore:'),
                sg.InputText(key='main.datasets_to_ignore', metadata={'type': str, 'clean': clean_comma_seperated_list}),
                sg.Text('Comma-separated value')
            ],
            [
                sg.Text('Allow extra columns?'),
                sg.Checkbox('Yes', key='main.extra_columns_ok', metadata={'type': bool})
            ],
            [
                sg.Text('Action'),
                sg.DropDown(sorted(list(__actions__.keys())), key='main.action', metadata={'type': str})
            ]
        ]

        for action in __actions__:
            layout.extend(self._get_window_action_layout(action))

        if __stdout_destination__ == StdOutDest.GUI:
            layout.extend([
                [
                    sg.Output(size=(200, 30), key='log')
                ]
            ])

        layout.extend([
            [
                sg.Button('Start'),
                sg.Button('Stop', disabled=True),
                sg.Exit()
            ]
        ])

        return layout

    def _get_window_action_layout(self, action):
        action_class = __actions__[action]
        layout = []

        for option, option_nice_name, option_type in action_class.CONFIG:
            key = f'action.{action}.{option}'

            text = sg.Text(f'Action / {action_class.NAME} / {option_nice_name}:')

            if option_type == str:
                input = sg.InputText(key=key, metadata={'type': str})
            elif option_type == bool:
                input = sg.Checkbox('Yes', key=key, metadata={'type': bool})

            layout.append([text, input])

        return layout

    def _load_config_into_window(self):
        input_pattern = re.compile('^(?P<section>[a-z][a-z]*(?:\.[a-z][a-z_]*)*)\.(?P<option>[a-z][a-z_]*)$')

        for win_key in self._window.key_dict:
            if (m := input_pattern.match(win_key)) is None:
                continue

            section, option = m.groups()

            if not config.has_option(section, option):
                continue

            # Decode values based on type of input
            if self._window[win_key].metadata['type'] == bool:
                value = config.getboolean(section, option)
            elif self._window[win_key].metadata['type'] == int:
                value = config.getint(section, option)
            else:
                value = config.get(section, option)

            self._window[win_key].update(value)

    def _get_main_config(self, values):
        main_config = {}

        main_config['datasets_path'] = values['main.datasets_path']
        main_config['datasets_to_process'] = [x for x in map(str.strip, values['main.datasets_to_process'].split(',')) if x]
        main_config['datasets_to_ignore'] = [x for x in map(str.strip, values['main.datasets_to_ignore'].split(',')) if x]
        main_config['extra_columns_ok'] = values['main.extra_columns_ok']
        main_config['action'] = values['main.action']

        return main_config

    def _get_action_config(self, action, values):
        action_config = dict()
        action_config_pattern = re.compile('^action\.(?P<action>[a-z][a-z_]*)\.(?P<param>[a-z][a-z_]*)$')

        for key, value in values.items():
            if m := action_config_pattern.match(key):
                config_action, config_param = m.groups()

                if config_action != action:
                    continue

                action_config[config_param] = value

        return action_config

    def _save_config(self, values):
        input_pattern = re.compile('^(?P<section>[a-z][a-z]*(?:\.[a-z][a-z_]*)*)\.(?P<option>[a-z][a-z_]*)$')

        for win_key, win_value in values.items():
            if (m := input_pattern.match(win_key)) is None:
                continue

            section, option = m.groups()

            if not config.has_section(section):
                config.add_section(section)

            # Clean value if necessary
            if hasattr(self._window[win_key].metadata, 'clean'):
                clean_fn = self._window[win_key].metadata['clean']
                win_value = clean_fn(win_value)

            # Encode values if necessary
            if self._window[win_key].metadata['type'] == bool:
                win_value = bool_to_ini_bool(win_value)
            elif self._window[win_key].metadata['type'] == int:
                win_value = int(win_value)

            config.set(section, option, win_value)

        config.save()

    # Event handlers

    def _handle_event(self, event, values):
        handler_fn = getattr(self, f'_handle_event__{event.lower()}')
        handler_fn(values)

    def _handle_event__start(self, values):
        self._save_config(values)

        self.disable_buttons('Start')
        self.enable_buttons('Stop')
        self.clear_log()

        self._stop_thread = False

        main_config = self._get_main_config(values)
        action_config = self._get_action_config(main_config['action'], values)

        kwargs = {
            'config': {'main': main_config, 'action': action_config},
            'get_stop_request': self._get_stop_request,
            'event_triggers': {'stopped': self._stopped, 'done': self._done}
        }

        Action = __actions__[main_config['action']]
        action = Action(**kwargs)

        self._thread = threading.Thread(target=action.run, daemon=True)
        self._thread.start()

    def _handle_event__done(self, values):
        self.enable_buttons('Start')
        self.disable_buttons('Stop')

        print('Done!')

    def _handle_event__stop(self, values):
        self.disable_buttons('Stop')

        self._stop_thread = True

    def _handle_event__stopped(self, values):
        print('Stopped!')

        self._stop_thread = False

        self.enable_buttons('Start')
        self.disable_buttons('Stop')

    # Trigger events

    def _stopped(self):
        self._window.write_event_value('Stopped', '')

    def _done(self):
        self._window.write_event_value('Done', '')

    # Controls

    def disable_buttons(self, *buttons):
        for button in buttons:
            self._window[button].update(disabled=True)

    def enable_buttons(self, *buttons):
        for button in buttons:
            self._window[button].update(disabled=False)

    def clear_log(self):
        if __stdout_destination__ == StdOutDest.TERMINAL:
            os.system('cls' if os.name == 'nt' else 'clear')

        if __stdout_destination__ == StdOutDest.GUI:
            self._window['log'].update('')

    # Task functions

    def _get_stop_request(self):
        return self._stop_thread


def clean_comma_seperated_list(l):
    return ', '.join(filter(None, map(str.strip, l.split(','))))


def bool_to_ini_bool(b):
    return 'yes' if b else 'no'


def ini_bool_to_bool(b):
    return b == 'yes'
