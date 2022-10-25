from argparse import ArgumentParser
import pathlib
import sys

from .actions import __actions__


def main():
    args = get_parsed_args()

    if args.gui:
        from . import gui
        gui.main()
    else:
        config = parsed_args_to_action_config(args)
        execute_action(args.action, config)


def get_parsed_args():
    parser = ArgumentParser()

    parser.add_argument('--gui', action='store_true')

    parser.add_argument('--datasets-path', required=('--gui' not in sys.argv), type=pathlib.Path)
    parser.add_argument('--datasets-to-process', metavar='DATASET_NAME', default=list(), nargs='*')
    parser.add_argument('--datasets-to-ignore', metavar='DATASET_NAME', default=list(), nargs='*')
    parser.add_argument('--extra-columns-ok', action='store_true')
    parser.add_argument('--action', required=('--gui' not in sys.argv), choices=__actions__.keys())

    # Add action arguments

    for action_name, action_class in __actions__.items():
        for option_name, option_nice_name, option_type in action_class.CONFIG:
            args = [
                f'--action.{action_name.replace("_", "-")}.{option_name.replace("_", "-")}'
            ]
            kwargs = {
                'help': option_nice_name,
                'type': option_type
            }

            if option_type == bool:
                kwargs['choices'] = {True, False}
                kwargs['default'] = False

            parser.add_argument(*args, **kwargs)

    return parser.parse_args()


def parsed_args_to_action_config(args):
    config = {
        'main': {
            'datasets_path': args.datasets_path,
            'datasets_to_process': args.datasets_to_process,
            'datasets_to_ignore': args.datasets_to_ignore,
            'extra_columns_ok': args.extra_columns_ok,
        },
        'action': {}
    }

    for key, value in args._get_kwargs():
        if not key.startswith(f'action.{args.action}.'):
            continue

        config['action'][key.split('.')[2]] = value

    return config


def execute_action(name, config):
    Action = __actions__[name]
    action_instance = Action(config=config)
    action_instance.run()


if __name__ == '__main__':
    main()
