from argparse import ArgumentParser
import os
from pathlib import Path

from commands import import_excel_datasets

if os.getenv('DEBUG_PYTHON', 'False') == 'True':
    import ipdb

DB_PATH_ARGUMENT_HELP       = "Path to an Geochem SQLite database file. One will be created if none exists at that path."
DATASETS_PATH_ARGUMENT_HELP = "Path to the directory containing Excel dataset directories."
REPLACE_ARGUMENT_HELP       = "Whether to recreate the Geochem SQLite database file if one exists at the given path."
DATASET_NAME_ARGUMENT_HELP  = "Name of the dataset to import."

def main():
    parser = ArgumentParser()

    subparsers = parser.add_subparsers()

    import_excel_datasets_parser = subparsers.add_parser('import_excel_datasets', help='import Excel datasets into a Geochem SQLite database')
    import_excel_datasets_parser.add_argument('db_path', type=Path, help=DB_PATH_ARGUMENT_HELP, metavar='DB_PATH')
    import_excel_datasets_parser.add_argument('datasets_path', type=Path, help=DATASETS_PATH_ARGUMENT_HELP, metavar='DATASETS_PATH')
    import_excel_datasets_parser.add_argument('--dataset-name', '-n', type=str, help=DATASET_NAME_ARGUMENT_HELP, metavar='DATASET_NAME')
    import_excel_datasets_parser.add_argument('--replace', '-r', action='store_true', help=REPLACE_ARGUMENT_HELP)
    args = parser.parse_args()

    if 'import_excel_datasets':
        command = import_excel_datasets.main
        command(args.db_path, args.datasets_path, dataset_name=args.dataset_name, replace=args.replace)


if __name__ == '__main__':
    main()
