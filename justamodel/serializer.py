# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod
import json
import collections
from .exceptions import ValidationError, ModelValidationError
from .model import get_type_specifier_name, get_model_class_for_type, get_type_name_for_model, Model
from .types import ModelType, StringType, BooleanType, IntType


class FieldSerializer():
    @abstractmethod
    def serialize_field(self, value, model_type, field_name, field, **kwargs):
        raise TypeError('Don\'t know how to serialize {}'.format(field.type))  # pragma: no cover

    @abstractmethod
    def deserialize_field(self, value, model_type, field_name, field, **kwargs):
        raise TypeError('Don\'t know how to deserialize {}'.format(field.type))  # pragma: no cover


class VerbatimFieldSerializer(FieldSerializer):
    def serialize_field(self, value, model_type, field_name, field, **kwargs):
        return value

    def deserialize_field(self, value, model_type, field_name, field, **kwargs):
        return value


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
    def __init__(self, field_serializer):
        self.field_serializer = field_serializer

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


class DictModelSerializer(ModelSerializer):
    def _serialize_model(self, value, model_type, **kwargs):
        if value is None:
            return None

        model_class = type(value)

        result = {}
        for name, field in self._iter_model_fields(model_class, **kwargs):
            if isinstance(field.type, ModelType):
                result[name] = self._serialize_model(getattr(value, name), model_class, **kwargs)
            else:
                result[name] = self.field_serializer.serialize_field(getattr(value, name), model_class, name, field,
                                                                     **kwargs)

        type_specifier_name = get_type_specifier_name(model_type)
        if type_specifier_name:
            model_type_name = get_type_name_for_model(model_type, model_class)
            result[type_specifier_name] = model_type_name

        return result

    def _deserialize_model(self, value, model_or_model_type, **kwargs):
        if value is None:
            return None

        if not isinstance(value, dict):
            raise ValidationError('Model deserialization requires dictionary type')

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

        for name, field in self._iter_model_fields(model_class, **kwargs):
            if isinstance(field.type, ModelType):
                deserialized_value = self._deserialize_model(value.get(name), field.type.native_type, **kwargs)
            else:
                deserialized_value = self.field_serializer.deserialize_field(value.get(name), model_class, name, field,
                                                                             **kwargs)
            setattr(model, name, deserialized_value)

        return model


class JsonModelSerializer(DictModelSerializer):
    def __init__(self, field_serializer, sort_keys=False):
        super().__init__(field_serializer)
        self.sort_keys = sort_keys

    def serialize_model(self, value, model_type=None, **kwargs):
        return json.dumps(super().serialize_model(value, model_type, **kwargs), sort_keys=self.sort_keys)

    def _deserialize_model(self, value, model_or_model_type, **kwargs):
        try:
            value = json.loads(value)
        except ValueError as e:
            raise ValidationError('Value is not a valid JSON: ' + str(e))
        return super()._deserialize_model(value, model_or_model_type, **kwargs)