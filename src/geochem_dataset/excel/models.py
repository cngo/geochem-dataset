from __future__ import annotations

from dataclasses import dataclass, field, fields

Extra = dict[str, str]


@dataclass
class Document:
    row_idx: int
    recommended_citation: str
    extra: Extra = field(default_factory=dict)


@dataclass
class Survey:
    row_idx: int
    title: str
    organization: str
    year_begin: int
    year_end: int
    party_leader: str
    description: str
    gsc_catalog_number: str
    extra: Extra = field(default_factory=dict)

    def __post_init__(self):
        self._cast_fields()

    def _cast_fields(self):
        if not isinstance(self.gsc_catalog_number, str):
            self.gsc_catalog_number = str(self.gsc_catalog_number)


@dataclass
class Sample:
    row_idx: int
    surveys_row_idx: int
    station: str
    earthmat: str
    name: str
    lat_nad27: float
    long_nad27: float
    lat_nad83: float
    long_nad83: float
    x_nad27: float
    y_nad27: float
    x_nad83: float
    y_nad83: float
    zone: str
    earthmat_type: str
    status: str
    extra: Extra = field(default_factory=dict)


@dataclass
class Result:
    worksheet: str
    cell: str
    sample_row_idx: int
    subsample: tuple[str, ...]
    type: str
    metadata_set: dict[str, str]
    value: str
