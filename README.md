# Geochemistry Dataset

This library provides an interface for managing geochemistry datasets.

It is based on the specification presented in the Summary of Activities 2019 volume.


## Requirements

- Python >=3.8
- pipenv



## Usage


Prepare the environment:

    pipenv install --python 3.9
    pipenv shell


### Excel

```python

from geochem_dataset.excel import Dataset

d = Dataset("DATASETS/COMPLETE/ca.cngo.gds-2021-001")


for document in dataset.documents:
    print(document)

for survey in dataset.surveys:
    print(survey)

for sample in dataset.samples:
    print(sample)

for result in dataset.analysis_bulk_results:
    print(result)

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


## Figures

### BULK.xlsx worksheet structure

| SAMPLE   | SUBSAMPLE   | ... | SUB...SUBSAMPLE   | METADATA_TYPE   | result_type_1 | ... | result_type_y |
|----------|-------------|-----|-------------------|-----------------|---------------|-----|---------------|
|          |             |     |                   | metadata_type_1 | metadata_1_1  | ... | metadata_1_y  |
|          |             |     |                   | ...             | ...           | ... | ...           |
|          |             |     |                   | metadata_type_z | metadata_z_1  | ... | metadata_z_y  |
| sample_1 | subsample_1 | ... | sub...subsample_1 |                 | result_1_1    | ... | result_1_y    |
| ...      | ...         | ... | ...               |                 | ...           | ... | ...           |
| sample_x | subsample_x | ... | sub...subsample_x |                 | result_x_1    | ... | result_x_y    |
