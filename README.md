# Geochemistry Dataset

This library provides an interface for managing geochemistry datasets.

It is based on the specification presented in the Summary of Activities 2019 volume.


## Requirements

- Python 3.9
- pipenv


## Usage

Prepare the environment:

    pipenv install --python 3.9
    pipenv shell


### Excel

In Python:

    from geochem_dataset.excel import Dataset

    path = "C:/Users/Duchess/Desktop/Datasets/ca.cngo.gds-2021-001
    dataset = Dataset(path)

    print(list(dataset.documents))
    print(list(dataset.surveys))
    print(list(dataset.samples))
    print(list(dataset.analysis_bulk_results))

The iterators above, e.g. `dataset.documents`, will yield items as frozen dataclasses. See `src/geochem_dataset.excel/dataclasses.py` for their definitions.


### Tools

A console script was installed for using the tools. Get help with its usage:

    geochem-dataset-tools --help

A GUI application can be launched by using the `--gui` flag:

    geochem-dataset-tools --gui


## Testing

Prepare the environment:

    pipenv install --python 3.9
    pipenv shell

Run the tests:

    tox
