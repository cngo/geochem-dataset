# Geochemistry Dataset Excel

This library provides an interface for reading geochemistry datasets that are in the format of a directory of Microsoft Excel files.

It is based on the specification presented in the Summary of Activities 2019 volume.


## Requirements

- Python 3.9
- pipenv


## Usage

Prepare the environment:

    pipenv install --python 3.9
    pipenv shell

In Python:

    from geochem_dataset_excel import Dataset

    path = "C:/Users/Duchess/Desktop/Datasets/ca.cngo.gds-2021-001
    dataset = Dataset(path)

    print(list(dataset.documents))
    print(list(dataset.surveys))
    print(list(dataset.samples))
    print(list(dataset.analysis_bulk_results))

The iterators above, e.g. `dataset.documents`, will yield items as frozen dataclasses. See `src/geochem_dataset_excel/dataclasses.py` for their definitions.


## Testing

Prepare the environment:

    pipenv install --python 3.9
    pipenv shell

Run the tests:

    tox
