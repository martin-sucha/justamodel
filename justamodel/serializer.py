# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod
import json
import collections
from collections.abc import Mapping
from .exceptions import ValidationError, ModelValidationError
from .model import get_type_specifier_name, get_model_class_for_type, get_type_name_for_model, Model
from .types import ModelType, StringType, BooleanType, IntType, ListType, SetType, DictType


def make_field_filter(fields):
    if fields is None:
        return lambda x: True
    if isinstance(fields, collections.Container):
        return lambda x: x[0] in fields
    else:
        return fields


def iter_model_fields(model_class, fields=None, **kwargs):
    items = model_class.fields.items()
    if fields is None:
        return items

    return filter(make_field_filter(fields), items)


class ModelSerializer(metaclass=ABCMeta):
    def __init__(self):
        pass

    def _iter_model_fields(self, model_class, **kwargs):
        return iter_model_fields(model_class, **kwargs)

    @abstractmethod
    def _serialize_model(self, value, model_type, **kwargs):
        raise NotImplementedError()  # pragma: no cover

    def serialize_model(self, value, model_type=None, **kwargs):
        if not isinstance(value, Model):
            raise TypeError('Value is not an instance of Model')
        if model_type is None:
            model_type = type(value)
        return self._serialize_model(value, model_type)

    @abstractmethod
    def _deserialize_model(self, value, model_type, **kwargs):
        raise NotImplementedError()  # pragma: no cover

    def deserialize_model(self, value, model_or_model_type, **kwargs):
        try:
            return self._deserialize_model(value, model_or_model_type, **kwargs)
        except ModelValidationError:
            raise  # pragma: no cover
        except ValidationError as e:
            mve = ModelValidationError()
            mve.__cause__ = e
            mve.add_error(e)
            raise mve

    def serialize_value(self, value, value_type, field=None, **kwargs):
        if isinstance(value_type, ModelType):
            return self._serialize_model(value, value_type.native_type, **kwargs)
        elif isinstance(value_type, ListType) and value is not None:
            return [self.serialize_value(x, value_type.item_type) for x in value]
        elif isinstance(value_type, SetType) and value is not None:
            return set([self.serialize_value(x, value_type.item_type) for x in value])
        elif isinstance(value_type, DictType) and value is not None:
            return {self.serialize_value(k, value_type.key_type): self.serialize_value(v, value_type.value_type)
                    for k, v in value.items()}
        return value

    def deserialize_value(self, value, value_type, field=None, **kwargs):
        if isinstance(value_type, ModelType):
            return self._deserialize_model(value, value_type.native_type, **kwargs)
        elif isinstance(value_type, ListType) and value is not None:
            return [self.deserialize_value(x, value_type.item_type) for x in value]
        elif isinstance(value_type, SetType) and value is not None:
            return set([self.deserialize_value(x, value_type.item_type) for x in value])
        elif isinstance(value_type, DictType) and value is not None:
            return {self.deserialize_value(k, value_type.key_type): self.deserialize_value(v, value_type.value_type)
                    for k, v in value.items()}
        return value


class DictModelSerializer(ModelSerializer):
    def __init__(self, mapping_type=dict):
        super().__init__()
        self.mapping_type = mapping_type

    def _serialize_model(self, value, model_type, **kwargs):
        if value is None:
            return None

        model_class = type(value)

        result = self.mapping_type()
        for name, field in self._iter_model_fields(model_class, **kwargs):
            result[name] = self.serialize_value(getattr(value, name), field.type, field=field, **kwargs)

        type_specifier_name = get_type_specifier_name(model_type)
        if type_specifier_name:
            model_type_name = get_type_name_for_model(model_type, model_class)
            result[type_specifier_name] = model_type_name

        return result

    def _deserialize_model(self, value, model_or_model_type, **kwargs):
        if value is None:
            return None

        if not isinstance(value, Mapping):
            raise ValidationError('Model deserialization requires mapping type')

        if isinstance(model_or_model_type, Model):
            model = model_or_model_type
            model_class = type(model)
        else:
            type_name = None
            type_specifier_name = get_type_specifier_name(model_or_model_type)
            if type_specifier_name is not None:
                if type_specifier_name not in value:
                    raise ValidationError('Polymorphic model requires type specifier')
                type_name = value[type_specifier_name]

            model_class = get_model_class_for_type(model_or_model_type, type_name)
            model = model_class()

        error = ModelValidationError()
        for name, field in self._iter_model_fields(model_class, **kwargs):
            try:
                deserialized_value = self.deserialize_value(value.get(name), field.type, field=field, **kwargs)
            except ValidationError as field_error:
                error.add_sub_error(name, field_error)
            else:
                setattr(model, name, deserialized_value)

        if error:
            raise error

        return model


class JsonModelSerializer(DictModelSerializer):
    def __init__(self, sort_keys=False):
        super().__init__()
        self.sort_keys = sort_keys

    def serialize_model(self, value, model_type=None, **kwargs):
        return json.dumps(super().serialize_model(value, model_type, **kwargs), sort_keys=self.sort_keys)

    def _deserialize_model(self, value, model_or_model_type, **kwargs):
        try:
            value = json.loads(value)
        except ValueError as e:
            raise ValidationError('Value is not a valid JSON: ' + str(e))
        return super()._deserialize_model(value, model_or_model_type, **kwargs)