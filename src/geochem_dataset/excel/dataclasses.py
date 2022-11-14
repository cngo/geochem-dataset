from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, Tuple


Extra = Dict[str, str]


@dataclass(frozen=True)
class Document:
    recommended_citation: str
    extra: Extra = field(default_factory=dict)


@dataclass(frozen=True)
class Survey:
    title: str
    organization: str
    year_begin: int
    year_end: int
    party_leader: str
    description: str
    gsc_catalog_number: int
    extra: Extra = field(default_factory=dict)


@dataclass(frozen=True)
class Sample:
    survey: Survey
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


ResultSubsample = Tuple[str, ...]
ResultMetadata = Dict[str, str]


@dataclass(frozen=True)
class Result:
    sample: str
    subsample: ResultSubsample
    type: str
    metadata: ResultMetadata
    value: str
