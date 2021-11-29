from dataclasses import dataclass, field


@dataclass(frozen=True)
class Document:
    recommended_citation: str

    extra: frozenset[tuple[str, str], ...] = field(default_factory=frozenset)  # key-value pairs


@dataclass(frozen=True)
class Survey:
    title: str
    organization: str
    year_begin: int
    year_end: int
    party_leader: str
    description: str
    gsc_catalog_number: int

    extra: frozenset[tuple[str, str], ...] = field(default_factory=frozenset)  # key-value pairs


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

    extra: frozenset[tuple[str, str], ...] = field(default_factory=frozenset)  # key-value pairs


@dataclass(frozen=True)
class Result:
    sample: Sample
    subsample: tuple[str, ...]
    type: str
    metadata: frozenset[tuple[str, str], ...]  # key-value pairs
    value: str
