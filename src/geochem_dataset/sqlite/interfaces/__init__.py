from typing import Iterator
import peewee

from .. import models
from .. import serializers
from .bases import SimpleForeignKeyInterface


class Config:
    __model__ = models.Config
    __serializer__ = serializers.Config

    def create(self, **kwargs):
        if 'id' in kwargs and kwargs['id'] is not None:
            raise ValueError("`id` must be `None` when creating")

        self.__serializer__(**kwargs)  # validate
        m = self.__model__(**kwargs)

        try:
            rows_modified = m.save()
        except peewee.IntegrityError as e:
            if e.args[0].startswith("UNIQUE constraint failed:"):
                raise ValueError(f"`{self.__model__}` already exists")

        if rows_modified == 0:
            raise Exception('FAILED')

        return self.__serializer__.from_row(m)

    def get_by_id(self, id):
        m = self.__model__.get_by_id(id)
        return self.__serializer__.from_row(m)

    def get_by_name(self, name):
        m = self.__model__.get(self.__model__.name == name)
        return self.__serializer__.from_row(m)

    def __iter__(self):
        q = self.__model__.select()

        for row in q.iterator():
            yield self.__serializer__.from_row(row)


class Datasets:
    __model__ = models.Dataset
    __serializer__ = serializers.Dataset

    def create(self, **kwargs) -> serializers.Dataset:
        if 'id' in kwargs and kwargs['id'] is not None:
            raise TypeError("`id` must be `None` when creating")

        self.__serializer__(**kwargs)  # validate
        m = self.__model__(**kwargs)

        try:
            rows_modified = m.save()
        except peewee.IntegrityError as e:
            if e.args[0].startswith("UNIQUE constraint failed:"):
                raise ValueError(f"`{self.__model__}` already exists")

        if rows_modified == 0:
            raise Exception('FAILED')

        return self.__serializer__.from_row(m)

    def get_by_id(self, id: int) -> serializers.Dataset:
        if not isinstance(id, int):
            raise TypeError(f'`id` must be of type `int`')

        try:
            m = self.__model__.get_by_id(id)
            return self.__serializer__.from_row(m)
        except self.__model__.DoesNotExist:
            return None

    def get_by_name(self, name: str) -> serializers.Dataset:
        if not isinstance(name, str):
            raise TypeError(f'`name` must be of type `str`')

        try:
            m = self.__model__.get(self.__model__.name == name)
            return self.__serializer__.from_row(m)
        except self.__model__.DoesNotExist:
            return None

    def __iter__(self) -> Iterator[serializers.Dataset]:
        q = self.__model__.select()

        for row in q.iterator():
            yield self.__serializer__.from_row(row)


class Documents(SimpleForeignKeyInterface):
    __model__ = models.Document
    __fk_field__ = models.Document.dataset_id
    __serializer__ = serializers.Document

    def get_by_recommended_citation(self, recommended_citation: str) -> serializers.Document:
        if not isinstance(recommended_citation, str):
            raise TypeError(f'`recommended_citation` must be of type `str`')

        try:
            m = self.__model__.get(
                self.__model__.dataset_id == self.fk_id,
                self.__model__.recommended_citation == recommended_citation
            )
            return self.__serializer__.from_row(m)
        except self.__model__.DoesNotExist:
            return None

class Surveys(SimpleForeignKeyInterface):
    __model__ = models.Survey
    __fk_field__ = models.Survey.dataset_id
    __serializer__ = serializers.Survey

    def get_by_title(self, title: str) -> serializers.Document:
        if not isinstance(title, str):
            raise TypeError(f'`title` must be of type `str`')

        try:
            m = self.__model__.get(
                self.__model__.dataset_id == self.fk_id,
                self.__model__.title == title
            )
            return self.__serializer__.from_row(m)
        except self.__model__.DoesNotExist:
            return None


class Samples(SimpleForeignKeyInterface):
    __model__ = models.Sample
    __fk_field__ = models.Sample.survey_id
    __serializer__ = serializers.Sample


class Subsamples(SimpleForeignKeyInterface):
    __model__ = models.Subsample
    __fk_field__ = models.Subsample.sample_id
    __serializer__ = serializers.Subsample


class SubsampleChildren:
    __model__ = models.Subsample
    __serializer__ = serializers.Subsample

    def __init__(self, parent_id):
        self.parent_id = parent_id

    def __iter__(self):
        q = self.__model__.select(). \
            where(self.__model__.parent_id == self.parent_id)

        for row in q.iterator():
            yield self.__serializer__.from_row(row)

    def create(self, **kwargs):
        for field in ('id', 'sample_id', 'parent_id'):
            if field in kwargs and kwargs[field] is not None:
                raise TypeError(f"`{field}` must be `None` when creating")

        parent = models.Subsample.get_by_id(self.parent_id)

        kwargs['sample_id'] = parent.sample_id
        kwargs['parent_id'] = self.parent_id

        self.__serializer__(**kwargs)  # validate
        m = self.__model__(**kwargs)

        try:
            rows_modified = m.save()
        except peewee.IntegrityError as e:
            if e.args[0].startswith("UNIQUE constraint failed:"):
                raise ValueError(f"`{self.__model__}` already exists")
            else:
                raise e

        if rows_modified == 0:
            raise Exception('FAILED')

        return self.__serializer__.from_row(m)


class MetadataSets(SimpleForeignKeyInterface):
    __model__ = models.MetadataSet
    __fk_field__ = models.MetadataSet.dataset_id
    __serializer__ = serializers.MetadataSet


class MetadataTypes(SimpleForeignKeyInterface):
    __model__ = models.MetadataType
    __fk_field__ = models.MetadataType.dataset_id
    __serializer__ = serializers.MetadataType


class Metadata:
    __model__ = models.Metadata
    __fk_field__ = models.Metadata.metadata_set_id
    __serializer__ = serializers.Metadata

    def __init__(self, metadata_set_id):
        self.metadata_set_id = metadata_set_id

    def __iter__(self):
        q = models.Result.select(). \
            join(models.Metadata). \
            where(models.Metadata.metadata_set_id == self.metadata_set_id)

        for row in q.iterator():
            yield serializers.Metadata.from_row(row)

    def create(self, **kwargs):
        for field in ('id', 'metadata_set_id'):
            if field in kwargs and kwargs[field] is not None:
                raise TypeError(f"`{field}` must be `None` when creating")

        kwargs['metadata_set_id'] = self.metadata_set_id

        self.__serializer__(**kwargs)  # validate
        m = self.__model__(**kwargs)

        try:
            rows_modified = m.save()
        except peewee.IntegrityError as e:
            if e.args[0].startswith("UNIQUE constraint failed:"):
                raise ValueError(f"`{self.__model__}` already exists")
            else:
                raise e

        if rows_modified == 0:
            raise Exception('FAILED')

        return self.__serializer__.from_row(m)


class ResultTypes(SimpleForeignKeyInterface):
    __model__ = models.ResultType
    __fk_field__ = models.ResultType.dataset_id
    __serializer__ = serializers.ResultType


class ResultsByDataset:
    __model__ = models.Result
    __serializer__ = serializers.Result

    def __init__(self, dataset_id):
        self.dataset_id = dataset_id

    def __iter__(self):
        q = models.Result.select(). \
            join(models.ResultType). \
            where(models.ResultType.dataset_id == self.dataset_id)

        for row in q.iterator():
            yield serializers.Result.from_row(row)

    def create(self, **kwargs):
        if 'id' in kwargs and kwargs['id'] is not None:
            raise TypeError("`id` must be `None` when creating")

        self.__serializer__(**kwargs)  # validate
        m = self.__model__(**kwargs)

        try:
            rows_modified = m.save()
        except peewee.IntegrityError as e:
            if e.args[0].startswith("UNIQUE constraint failed:"):
                raise ValueError(f"`{self.__model__}` already exists")
            else:
                raise e

        if rows_modified == 0:
            raise Exception('FAILED')

        return self.__serializer__.from_row(m)
