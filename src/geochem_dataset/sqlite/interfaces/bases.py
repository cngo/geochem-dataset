from typing import Union
import peewee

from geochem_dataset.sqlite import serializers


# class BaseInterface:
#     def create(self, **kwargs):
#         if 'id' in kwargs and kwargs['id'] is not None:
#             raise TypeError("`id` must be `None` when creating")

#         dataset = self.Meta.serializer(**kwargs)

#         model_instance = self.Meta.model(**kwargs)

#         try:
#             rows_modified = model_instance.save()
#         except peewee.IntegrityError as e:
#             if e.args[0].startswith("UNIQUE constraint failed:"):
#                 raise ValueError(f"`{self.Meta.model}` already exists")

#         if rows_modified == 0:
#             raise Exception('FAILED')

#         return self.Meta.serializer.from_row(model_instance)

#     def get_by_id(self, id: int):
#         if not isinstance(id, int):
#             raise TypeError

#         try:
#             return self.Meta.model.get_by_id(id)
#         except self.Meta.model.DoesNotExist:
#             raise ValueError(f"`{self.Meta.model}` with `(id)=({id})` does not exist")

#     def get_by_name(self, name: str):
#         if not isinstance(name, str):
#             raise TypeError

#         try:
#             return self.Meta.model.get(name=name)
#         except self.Meta.model.DoesNotExist:
#             raise ValueError(f"`{self.Meta.model}` with `(name)=({name})` does not exist")

#     def __iter__(self):
#         order_by_items = [
#             getattr(getattr(self.Meta.model, field), dir)()
#             for field, dir in self.Meta.iter_order_by
#         ]

#         query = self.Meta.model.select().order_by(**order_by_items)

#         for dataset in query:
#             yield dataset


class SimpleForeignKeyInterface:
    def __init__(self, fk_id):
        self.fk_id = fk_id

    def __iter__(self):
        q = self.__model__.select(). \
            where(self.__fk_field__ == self.fk_id)

        for row in q.iterator():
            yield self.__serializer__.from_row(row)

    def create(self, **kwargs):
        if 'id' in kwargs and kwargs['id'] is not None:
            raise ValueError("`id` must be `None` when creating")

        fk_id_field_name = f'{self.__fk_field__.name}_id'
        kwargs[fk_id_field_name] = self.fk_id

        s = self.__serializer__(**kwargs)
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

    def get_by_id(self, id: int):
        if not isinstance(id, int):
            raise TypeError(f'`id` must be of type `int`')

        try:
            m = self.__model__.get(self.__model__.id == id, self.__fk_field__ == self.fk_id)
            return self.__serializer__.from_row(m)
        except self.__model__.DoesNotExist:
            return None
