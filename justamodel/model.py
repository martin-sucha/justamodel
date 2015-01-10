# -*- coding: utf-8 -*-
from collections import OrderedDict
from .exceptions import ValidationError, ModelValidationError
from abc import ABCMeta

type_default = object()


class Field:
    def __init__(self, type, required=True, default=type_default, **kwargs):
        self.required = required
        self.default = default
        self.type = type
        for name, value in kwargs.items():
            setattr(self, name, value)

    def create_default_value(self):
        if self.default is type_default:
            if not self.required:
                return None
            return self.type.default_value
        elif callable(self.default):
            return self.default()
        else:
            return self.default

    def validate(self, value):
        if value is None:
            if self.required:
                raise ValidationError('value is required')
        else:
            self.type.validate(value)


class ModelMeta(type):
    @classmethod
    def __prepare__(mcls, name, bases):
        return OrderedDict()

    def __new__(mcls, name, bases, namespace):
        declared_fields = OrderedDict()
        new_namespace = {}
        for key, value in namespace.items():
            if isinstance(value, Field):
                declared_fields[key] = value
            else:
                new_namespace[key] = value
        new_namespace['declared_fields'] = declared_fields

        cls = super().__new__(mcls, name, bases, new_namespace)

        merged_fields = OrderedDict()
        for part_cls in (part_cls for part_cls in reversed(cls.mro()) if hasattr(part_cls, 'declared_fields')):
            for key, field in part_cls.declared_fields.items():
                merged_fields[key] = field

        cls.fields = merged_fields

        return cls


class Model(metaclass=ModelMeta):
    fields = None

    def __init__(self, **kwargs):
        for name, field in self.fields.items():
            if name in kwargs:
                setattr(self, name, kwargs[name])
            else:
                setattr(self, name, field.create_default_value())

    def validate(self):
        error = ModelValidationError()
        for name, field in self.fields.items():
            try:
                field.validate(getattr(self, name))
            except ValidationError as field_error:
                error.add_field_error(name, field_error)
        if error:
            raise error

    def __eq__(self, other):
        if type(self) != type(other):
            return NotImplemented
        for name in self.fields.keys():
            if not (getattr(self, name) == getattr(other, name)):
                return False
        return True

    def __ne__(self, other):
        if type(self) != type(other):
            return NotImplemented
        for name in self.fields.keys():
            if getattr(self, name) != getattr(other, name):
                return True
        return False

    def __repr__(self):  # pragma: no cover
        field_descr = ', '.join('{}={!r}'.format(name, getattr(self, name)) for name in type(self).fields.keys())
        return '{}({})'.format(type(self).__qualname__, field_descr)


class PolymorphicModelMeta(ABCMeta):
    def __new__(mcs, name, bases, namespace):
        for klass in bases:
            if isinstance(klass, PolymorphicModelMeta) and klass is not PolymorphicModel:
                raise TypeError('Polymorphic models cannot be subclassed')

        cls = super().__new__(mcs, name, bases, namespace)
        cls.types_to_model_classes_mro = list(cls.types_to_model_classes.items())
        cls.types_to_model_classes_mro.sort(key=lambda x: len(x[1].mro()), reverse=True)
        return cls

    def __call__(self, type_name, *args, **kwargs):
        model_class = self.get_model_class_for_type(type_name)
        if model_class is None:
            raise ValueError('Unknown model type name {!r} for class {}'.format(type_name, self))
        return model_class(*args, **kwargs)


class PolymorphicModel(metaclass=PolymorphicModelMeta):
    types_to_model_classes = {}
    types_to_model_classes_mro = []
    type_specifier_name = 'type'

    @classmethod
    def get_model_type_for_class(cls, unknown_class):
        for type_name, model_class in cls.types_to_model_classes_mro:
            if issubclass(unknown_class, model_class):
                return type_name
        return None

    @classmethod
    def get_model_class_for_type(cls, type_name):
        return cls.types_to_model_classes.get(type_name)

    @classmethod
    def __subclasshook__(cls, C):
        if cls.get_model_type_for_class(C) is not None:
            return True
        return NotImplemented


def get_model_class_for_type(model_type, type_name):
    if not hasattr(model_type, 'get_model_class_for_type'):
        return model_type

    model_class = model_type.get_model_class_for_type(type_name)

    if model_class is None:
        raise ValidationError('{} is not in allowed types'.format(type_name))

    return model_class


def get_type_name_for_model(model_type, model_class):
    model_type_name = model_type.get_model_type_for_class(model_class)

    if model_type_name is None:
        raise TypeError('Could not determine model type name for {} using {}'.format(model_class, model_type))

    return model_type_name


def get_type_specifier_name(model_type):
    return getattr(model_type, 'type_specifier_name', None)