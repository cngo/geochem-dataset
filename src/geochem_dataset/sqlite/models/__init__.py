from peewee import Check
from playhouse.sqlite_ext import (
    DatabaseProxy, Model,
    CharField, FloatField, ForeignKeyField, IntegerField, JSONField
)

database_proxy = DatabaseProxy()


class BaseModel(Model):
    class Meta:
        database = database_proxy


class Config(BaseModel):
    name  = CharField(unique=True)
    value = CharField()

    class Meta:
        table_name = 'config'


class Dataset(BaseModel):
    name  = CharField(unique=True)
    extra = JSONField(null=True, default=None)

    class Meta:
        table_name = 'datasets'


class Document(BaseModel):
    dataset              = ForeignKeyField(Dataset, backref='documents')
    recommended_citation = CharField()
    extra                = JSONField(null=True, default=None)

    class Meta:
        table_name = 'documents'
        indexes = (
            (('dataset', 'recommended_citation'), True),
        )


class Survey(BaseModel):
    dataset            = ForeignKeyField(Dataset, backref='surveys')
    title              = CharField()
    organization       = CharField()
    year_begin         = IntegerField()
    year_end           = IntegerField(null=True)
    party_leader       = CharField(null=True, default=None)
    description        = CharField(null=True, default=None)
    gsc_catalog_number = IntegerField(null=True, default=None)
    extra              = JSONField(null=True, default=None)

    class Meta:
        table_name = 'surveys'
        indexes = (
            (('dataset', 'title'), True),
        )
        constraints = (
            Check('year_end IS NULL OR year_end >= year_begin'),
        )


class Sample(BaseModel):
    survey        = ForeignKeyField(Survey, backref='samples')
    station       = CharField()
    earthmat      = CharField()
    name          = CharField()
    lat_nad27     = FloatField(null=True)
    long_nad27    = FloatField(null=True)
    lat_nad83     = FloatField(null=True)
    long_nad83    = FloatField(null=True)
    x_nad27       = FloatField(null=True)
    y_nad27       = FloatField(null=True)
    x_nad83       = FloatField(null=True)
    y_nad83       = FloatField(null=True)
    zone          = CharField(null=True, default=None)
    earthmat_type = CharField()
    status        = CharField(null=True, default=None)
    extra         = JSONField(null=True, default=None)

    class Meta:
        table_name = 'samples'
        indexes = (
            (('survey', 'station', 'earthmat', 'name'), True),
        )
        constraints = (
            Check('(lat_nad27 IS NULL AND long_nad27 IS NULL) OR (lat_nad27 IS NOT NULL AND long_nad27 IS NOT NULL)'),
            Check('(lat_nad83 IS NULL AND long_nad83 IS NULL) OR (lat_nad83 IS NOT NULL AND long_nad83 IS NOT NULL)'),
            Check('(x_nad27 IS NULL AND y_nad27 IS NULL) OR (x_nad27 IS NOT NULL AND y_nad27 IS NOT NULL AND zone IS NOT NULL)'),
            Check('(x_nad83 IS NULL AND y_nad83 IS NULL) OR (x_nad83 IS NOT NULL AND y_nad83 IS NOT NULL AND zone IS NOT NULL)'),
        )


class Subsample(BaseModel):
    sample = ForeignKeyField(Sample, backref='subsamples')
    parent = ForeignKeyField('self', backref='children', null=True)
    name   = CharField()

    class Meta:
        table_name = 'subsamples'
        indexes = (
            (('sample', 'parent', 'name'), True),
        )


class ResultType(BaseModel):
    dataset = ForeignKeyField(Dataset, backref='result_types')
    name    = CharField()

    class Meta:
        table_name = 'result_types'
        indexes = (
            (('dataset', 'name'), True),
        )


class MetadataSet(BaseModel):
    dataset = ForeignKeyField(Dataset, backref='metadata_sets')

    class Meta:
        table_name = 'metadata_sets'


class MetadataType(BaseModel):
    dataset = ForeignKeyField(Dataset, backref='metadata_types')
    name = CharField()

    class Meta:
        table_name = 'metadata_types'
        indexes = (
            (('dataset', 'name'), True),
        )


class Metadata(BaseModel):
    set   = ForeignKeyField(MetadataSet, backref='items', column_name='metadata_set_id')
    type  = ForeignKeyField(MetadataType, backref='items', column_name='metadata_type_id')
    value = CharField(null=True)

    class Meta:
        table_name = 'metadata'
        indexes = (
            (('set', 'type'), True),
        )


class Result(BaseModel):
    subsample    = ForeignKeyField(Subsample, backref='results')
    type         = ForeignKeyField(ResultType, backref='results', column_name='result_type_id')
    metadata_set = ForeignKeyField(MetadataSet, backref='results')
    value        = CharField(null=True, default=None)

    class Meta:
        table_name = 'results'
        indexes = (
            (('subsample', 'type', 'metadata_set'), True),
        )
