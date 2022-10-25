from __future__ import annotations
from typing import Optional, Union

import attr
from attr.validators import deep_mapping, instance_of, matches_re, optional
from playhouse.shortcuts import model_to_dict

from .. import interfaces
from .. import models
from .validators import gte_other_attrib, not_empty_str, not_negative_int, valid_latitude, valid_longitude, other_attrib_given

DATASET_NAME_PATTERN = r'^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]$'  # reverse domain name notation


@attr.s(frozen=True)
class Config:
    id: int    = attr.ib(kw_only=True, default=None, validator=[optional(instance_of(int))])
    name: str  = attr.ib(kw_only=True, validator=[instance_of(str)])
    value: str = attr.ib(kw_only=True)

    @classmethod
    def from_row(cls, row):
        return cls(id=row.id, name=row.name, value=row.value)


@attr.s(frozen=False)
class Dataset:
    id: int     = attr.ib(kw_only=True, default=None, validator=[optional(instance_of(int))])
    name: str   = attr.ib(kw_only=True, validator=[instance_of(str), matches_re(DATASET_NAME_PATTERN)])
    extra: dict = attr.ib(kw_only=True, default=None, validator=[optional(deep_mapping(key_validator=instance_of(str), value_validator=instance_of(str), mapping_validator=instance_of(dict)))])

    @classmethod
    def from_row(cls, row: models.Dataset) -> Dataset:
        return cls(id=row.id, name=row.name, extra=row.extra)

    @property
    def documents(self) -> interfaces.Documents:
        return interfaces.Documents(self.id)

    @property
    def surveys(self) -> interfaces.Surveys:
        return interfaces.Surveys(self.id)

    @property
    def metadata_sets(self) -> interfaces.MetadataSets:
        return interfaces.MetadataSets(self.id)

    @property
    def metadata_types(self) -> interfaces.MetadataTypes:
        return interfaces.MetadataTypes(self.id)

    @property
    def result_types(self) -> interfaces.ResultTypes:
        return interfaces.ResultTypes(self.id)

    @property
    def results(self) -> interfaces.ResultsByDataset:
        return interfaces.ResultsByDataset(self.id)


@attr.s(frozen=True)
class Document:
    id: int                   = attr.ib(kw_only=True, default=None, validator=[optional(instance_of(int))])
    dataset_id: int           = attr.ib(kw_only=True, validator=[instance_of(int)])
    recommended_citation: str = attr.ib(kw_only=True, validator=[instance_of(str), not_empty_str])
    extra: dict               = attr.ib(kw_only=True, default=None, validator=[optional(deep_mapping(key_validator=instance_of(str), value_validator=instance_of(str), mapping_validator=instance_of(dict)))])

    @classmethod
    def from_row(cls, row: models.Document) -> Document:
        return cls(id=row.id, dataset_id=row.dataset_id, recommended_citation=row.recommended_citation, extra=row.extra)

    @property
    def dataset(self) -> Dataset:
        dataset = models.Dataset.get_by_id(self.dataset_id)
        return Dataset.from_row(dataset)


@attr.s(frozen=False)
class Survey:
    id: int                           = attr.ib(kw_only=True, default=None, validator=[optional(instance_of(int))])
    dataset_id: int                   = attr.ib(kw_only=True, validator=[instance_of(int)])
    title: str                        = attr.ib(kw_only=True, validator=[instance_of(str), not_empty_str])
    organization: str                 = attr.ib(kw_only=True, validator=[instance_of(str), not_empty_str])
    year_begin: int                   = attr.ib(kw_only=True, validator=[instance_of(int), not_negative_int])
    year_end: Optional[int]           = attr.ib(kw_only=True, default=None, validator=[optional([instance_of(int), not_negative_int, gte_other_attrib('year_begin')])])
    party_leader: str                 = attr.ib(kw_only=True, default=None, validator=[optional([instance_of(str)])])
    description: str                  = attr.ib(kw_only=True, default=None, validator=[optional([instance_of(str)])])
    gsc_catalog_number: Optional[int] = attr.ib(kw_only=True, default=None, validator=[optional(instance_of(int))])
    extra: dict                       = attr.ib(kw_only=True, default=None, validator=[optional(deep_mapping(key_validator=instance_of(str), value_validator=instance_of(str), mapping_validator=instance_of(dict)))])

    @classmethod
    def from_row(cls, row: models.Survey) -> Survey:
        return cls(id=row.id, dataset_id=row.dataset_id, title=row.title, organization=row.organization, year_begin=row.year_begin, year_end=row.year_end, party_leader=row.party_leader, description=row.description, gsc_catalog_number=row.gsc_catalog_number, extra=row.extra)

    @property
    def dataset(self) -> Dataset:
        dataset = models.Dataset.get_by_id(self.dataset_id)
        return Dataset.from_row(dataset)

    @property
    def samples(self) -> interfaces.Samples:
        return interfaces.Samples(self.id)


@attr.s(frozen=True)
class Sample:
    id: int            = attr.ib(kw_only=True, default=None, validator=[optional(instance_of(int))])
    survey_id: int     = attr.ib(kw_only=True, validator=[instance_of(int)])
    station: str       = attr.ib(kw_only=True, validator=[instance_of(str), not_empty_str])
    earthmat: str      = attr.ib(kw_only=True, validator=[instance_of(str), not_empty_str])
    name: str          = attr.ib(kw_only=True, validator=[instance_of(str), not_empty_str])
    lat_nad27: float   = attr.ib(kw_only=True, default=None, validator=[optional([instance_of(float), valid_latitude])])
    long_nad27: float  = attr.ib(kw_only=True, default=None, validator=[optional([instance_of(float), valid_longitude])])
    lat_nad83: float   = attr.ib(kw_only=True, default=None, validator=[optional([instance_of(float), valid_latitude])])
    long_nad83: float  = attr.ib(kw_only=True, default=None, validator=[optional([instance_of(float), valid_longitude])])
    x_nad27: float     = attr.ib(kw_only=True, default=None, validator=[optional([instance_of(float)])])
    y_nad27: float     = attr.ib(kw_only=True, default=None, validator=[optional([instance_of(float)])])
    x_nad83: float     = attr.ib(kw_only=True, default=None, validator=[optional([instance_of(float)])])
    y_nad83: float     = attr.ib(kw_only=True, default=None, validator=[optional([instance_of(float)])])
    zone: str          = attr.ib(kw_only=True, default=None, validator=[optional([instance_of(str), not_empty_str])])
    earthmat_type: str = attr.ib(kw_only=True, default=None, validator=[optional([instance_of(str), not_empty_str])])
    status: str        = attr.ib(kw_only=True, default=None, validator=[optional([instance_of(str), not_empty_str])])
    extra: dict        = attr.ib(kw_only=True, default=None, validator=[optional(deep_mapping(key_validator=instance_of(str), value_validator=instance_of(str), mapping_validator=instance_of(dict)))])

    def __attrs_post_init__(self):
        # Validate lat/long coordinates

        if self.lat_nad27 is None and self.long_nad27 is not None:
            raise ValueError(f"'lat_nad27' must be given because 'long_nad27' is given")

        if self.lat_nad27 is not None and self.long_nad27 is None:
            raise ValueError(f"'long_nad27' must be given because 'lat_nad27' is given")

        if self.lat_nad83 is None and self.long_nad83 is not None:
            raise ValueError(f"'lat_nad83' must be given because 'long_nad83' is given")

        if self.lat_nad83 is not None and self.long_nad83 is None:
            raise ValueError(f"'long_nad83' must be given because 'lat_nad83' is given")

        # Validate UTM coordinates

        zone_given = self.zone is not None

        x_nad27_given = self.x_nad27 is not None
        y_nad27_given = self.y_nad27 is not None

        if any([x_nad27_given, y_nad27_given]):
            if not x_nad27_given:
                raise ValueError(f"'x_nad27' must be given because 'y_nad27' are given")

            if not y_nad27_given:
                raise ValueError(f"'y_nad27' must be given because 'x_nad27' are given")

            if not zone_given:
                raise ValueError(f"'zone' must be given because 'x_nad27' and/or 'y_nad27' are given")

        x_nad83_given = self.x_nad83 is not None
        y_nad83_given = self.y_nad83 is not None

        if any([x_nad83_given, y_nad83_given]):
            if not x_nad83_given:
                raise ValueError(f"'x_nad83' must be given because 'y_nad83' are given")

            if not y_nad83_given:
                raise ValueError(f"'y_nad83' must be given because 'x_nad83' are given")

            if not zone_given:
                raise ValueError(f"'zone' must be given because 'x_nad83' and/or 'y_nad83' are given")

    @classmethod
    def from_row(cls, row: models.Sample) -> Sample:
        return cls(id=row.id, survey_id=row.survey_id, station=row.station, earthmat=row.earthmat, name=row.name, lat_nad27=row.lat_nad27, long_nad27=row.long_nad27, lat_nad83=row.lat_nad83, long_nad83=row.long_nad83, x_nad27=row.x_nad27, y_nad27=row.y_nad27, x_nad83=row.x_nad83, y_nad83=row.y_nad83, zone=row.zone, earthmat_type=row.earthmat_type, status=row.status, extra=row.extra)

    @property
    def survey(self) -> Survey:
        survey = models.Survey.get_by_id(self.survey_id)
        return Survey.from_row(survey)

    @property
    def subsamples(self) -> interfaces.Subsamples:
        return interfaces.Subsamples(self.id)


@attr.s(frozen=True)
class Subsample:
    id: int        = attr.ib(kw_only=True, default=None, validator=[optional(instance_of(int))])
    sample_id: int = attr.ib(kw_only=True, default=None, validator=[instance_of(int)])
    parent_id: int = attr.ib(kw_only=True, default=None, validator=[optional(instance_of(int))])
    name: str      = attr.ib(kw_only=True, validator=[instance_of(str), not_empty_str])

    @classmethod
    def from_row(cls, row: models.Subsample) -> Subsample:
        return cls(id=row.id, sample_id=row.sample_id, parent_id=row.parent_id, name=row.name)

    @property
    def sample(self) -> Sample:
        sample = models.Sample.get_by_id(self.sample_id)
        return Sample.from_row(sample)

    @property
    def parent(self) -> Union[Subsample, None]:
        try:
            parent = models.Subsample.get_by_id(self.parent_id)
            return Subsample.from_row(parent)
        except models.Subsample.DoesNotExist:
            return None

    @property
    def children(self) -> interfaces.SubsampleChildren:
        return interfaces.SubsampleChildren(self.id)

    @property
    def results(self) -> interfaces.ResultsBySubsample:
        return interfaces.ResultsBySubsample(self.id)


@attr.s(frozen=True)
class MetadataSet:
    id: int = attr.ib(kw_only=True, default=None, validator=[optional(instance_of(int))])
    dataset_id: int = attr.ib(kw_only=True, validator=[instance_of(int)])

    @classmethod
    def from_row(cls, row: models.MetadataSet) -> MetadataSet:
        return cls(id=row.id, dataset_id=row.dataset_id)

    @property
    def items(self) -> interfaces.Metadata:
        return interfaces.Metadata(self.id)


@attr.s(frozen=True)
class MetadataType:
    id: int         = attr.ib(kw_only=True, default=None, validator=[optional(instance_of(int))])
    dataset_id: int = attr.ib(kw_only=True, validator=[instance_of(int)])
    name: str       = attr.ib(kw_only=True, validator=[instance_of(str), not_empty_str])

    @classmethod
    def from_row(cls, row: models.MetadataType) -> MetadataType:
        return cls(id=row.id, dataset_id=row.dataset_id, name=row.name)


@attr.s(frozen=True)
class Metadata:
    id: int      = attr.ib(kw_only=True, default=None, validator=[optional(instance_of(int))])
    set_id: int  = attr.ib(kw_only=True, validator=[instance_of(int)])
    type_id: int = attr.ib(kw_only=True, validator=[instance_of(int)])
    value: str   = attr.ib(kw_only=True, validator=[instance_of(str)])

    @classmethod
    def from_row(cls, row: models.Metadata) -> Metadata:
        return cls(id=row.id, set_id=row.set_id, type_id=row.type_id, value=row.value)

    @property
    def set(self) -> MetadataSet:
        set = models.MetadataSet.get_by_id(self.set_id)
        return MetadataSet.from_row(set)

    @property
    def type(self) -> MetadataType:
        type = models.MetadataType.get_by_id(self.type_id)
        return MetadataType.from_row(type)


@attr.s(frozen=True)
class ResultType:
    id: int         = attr.ib(kw_only=True, default=None, validator=[optional(instance_of(int))])
    dataset_id: int = attr.ib(kw_only=True, validator=[instance_of(int)])
    name: str       = attr.ib(kw_only=True, validator=[instance_of(str), not_empty_str])

    @classmethod
    def from_row(cls, row: models.ResultType) -> ResultType:
        return cls(id=row.id, dataset_id=row.dataset_id, name=row.name)


@attr.s(frozen=True)
class Result:
    id: int              = attr.ib(kw_only=True, default=None, validator=[optional(instance_of(int))])
    subsample_id: int    = attr.ib(kw_only=True, validator=[instance_of(int)])
    type_id: int         = attr.ib(kw_only=True, validator=[instance_of(int)])
    metadata_set_id: int = attr.ib(kw_only=True, validator=[instance_of(int)])
    value: str           = attr.ib(kw_only=True, validator=[instance_of(str)])

    @property
    def subsample(self) -> Subsample:
        subsample = models.Subsample.get_by_id(self.subsample_id)
        return Subsample.from_row(subsample)

    @property
    def result_type(self) -> str:
        result_type = models.ResultType.get_by_id(self.result_type_id)
        return result_type.name

    @property
    def metadata(self) -> dict:
        metadata_set = models.MetadataSet.get_by_id(self.metadata_set_id)
        metadata_set.metadata

    @classmethod
    def from_row(cls, row: models.Result) -> Result:
        return cls(id=row.id, subsample_id=row.subsample_id, type_id=row.type_id, metadata_set_id=row.metadata_set_id, value=row.value)
