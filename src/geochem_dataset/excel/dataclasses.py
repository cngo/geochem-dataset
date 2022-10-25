from __future__ import annotations

from dataclasses import dataclass, field
from typing import FrozenSet, Tuple

Extra = FrozenSet[Tuple[str, str]]


@dataclass(frozen=True)
class Document:
    recommended_citation: str
    extra: Extra = field(default_factory=frozenset)


@dataclass(frozen=True)
class Survey:
    title: str
    organization: str
    year_begin: int
    year_end: int
    party_leader: str
    description: str
    gsc_catalog_number: int
    extra: Extra = field(default_factory=frozenset)


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
    extra: Extra = field(default_factory=frozenset)


ResultSubsample = Tuple[str, ...]
ResultMetadata = FrozenSet[Tuple[str, str]]


@dataclass(frozen=True)
class Result:
    subsample: ResultSubsample
    type: str
    metadata: ResultMetadata
    value: str
