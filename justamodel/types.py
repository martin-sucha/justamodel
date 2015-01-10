# -*- coding: utf-8 -*-
from collections.abc import Iterable
from datetime import datetime, date, time
from importlib import import_module
from urllib.parse import urlparse
import re
import builtins
from .exceptions import ValidationError


class ValueType:
    def __init__(self, validators=None):
        if validators is None:
            self.validators = []
        else:
            self.validators = validators

    def validate(self, value):
        if not isinstance(value, self.native_type):
            raise ValidationError('{!r} is not an instance of {}'.format(value, self.native_type))
        for validator in self.validators:
            validator(value)

    @property
    def native_type(self):
        return object

    @property
    def default_value(self):
        return self.native_type()


class BooleanType(ValueType):
    @property
    def native_type(self):
        return bool


class SizedType(ValueType):
    def __init__(self, min_length=None, max_length=None, **kwargs):
        super().__init__(**kwargs)
        self.min_length = min_length
        self.max_length = max_length

    def validate(self, value):
        super().validate(value)
        if self.min_length is not None and len(value) < self.min_length:
            raise ValidationError('{!r} is too short, minimal allowed length is {} characters'
                                  .format(value, self.min_length))
        if self.max_length is not None and len(value) > self.max_length:
            raise ValidationError('{!r} is too long, maximal allowed length is {} characters'
                                  .format(value, self.max_length))


class ComparableType(ValueType):
    def __init__(self, min_value=None, max_value=None, **kwargs):
        super().__init__(**kwargs)
        self.min_value = min_value
        self.max_value = max_value

    def validate(self, value):
        super().validate(value)
        if self.min_value is not None and value < self.min_value:
            raise ValidationError('{!r} is too small, minimal allowed value is {!r}'.format(value, self.min_value))
        if self.max_value is not None and value > self.max_value:
            raise ValidationError('{!r} is too small, minimal allowed value is {!r}'.format(value, self.max_value))


class StringType(SizedType):
    def __init__(self, regex=None, **kwargs):
        super().__init__(**kwargs)
        if regex is None:
            self.regex = None
        elif isinstance(regex, str):
            self.regex = re.compile(regex)
        else:
            self.regex = regex

    @property
    def native_type(self):
        return str

    def validate(self, value):
        super().validate(value)
        if self.regex is not None and not self.regex.search(value):
            raise ValidationError('{!r} does not match validation pattern')


class UrlType(StringType):
    def __init__(self, scheme=None, **kwargs):
        super().__init__(**kwargs)
        if scheme is None:
            self.scheme = None
        elif isinstance(scheme, str):
            self.scheme = (scheme,)
        elif isinstance(scheme, Iterable):
            self.scheme = tuple(scheme)
        else:
            raise TypeError('Invalid value type {} for scheme constraint'.format(type(scheme)))

    def validate(self, value):
        super().validate(value)
        parsed = urlparse(value)
        if self.scheme is not None and parsed.scheme not in self.scheme:
            raise ValidationError('{!r} scheme is not {!r}'.format(value, self.scheme))


class IntType(ComparableType):
    @property
    def native_type(self):
        return int


class IterableType(SizedType):
    def __init__(self, item_type=None, **kwargs):
        super().__init__(**kwargs)
        self.item_type = item_type

    def validate(self, value):
        super().validate(value)
        if self.item_type is not None:
            for item in value:
                self.item_type.validate(item)


class ListType(IterableType):
    @property
    def native_type(self):
        return list


class SetType(IterableType):
    @property
    def native_type(self):
        return set


class DictType(SizedType):
    def __init__(self, key_type=None, value_type=None, **kwargs):
        super().__init__(**kwargs)
        self.key_type = key_type
        self.value_type = value_type

    @property
    def native_type(self):
        return dict

    def validate(self, value):
        super().validate(value)
        if self.key_type is not None or self.value_type is not None:
            for item_key, item_value in value.items():
                if self.key_type is not None:
                    self.key_type.validate(item_key)
                if self.value_type is not None:
                    self.value_type.validate(item_value)


def import_object(fully_qualified_name):
    parts = [part for part in fully_qualified_name.split('.') if part]

    module = None
    module_parts = 0
    part_count = len(parts)
    while module_parts < part_count:
        try:
            part_module = import_module('.'.join(parts[:module_parts+1]))
        except ImportError:
            break
        module_parts += 1
        module = part_module

    if module is None:
        module = builtins

    value = module
    for part in parts[module_parts:]:
        value = getattr(value, part)

    return value


class ModelType(ValueType):
    def __init__(self, model_class, **kwargs):
        super().__init__(**kwargs)
        self._model_class = model_class

    @property
    def model_class(self):
        if isinstance(self._model_class, str):
            self._model_class = import_object(self._model_class)
        return self._model_class

    @property
    def native_type(self):
        return self.model_class

    def validate(self, value):
        super().validate(value)
        if value is not None:
            value.validate()


class DateTimeType(ComparableType):
    @property
    def native_type(self):
        return datetime

    @property
    def default_value(self):
        return datetime.now()


class DateType(ComparableType):
    @property
    def native_type(self):
        return date

    @property
    def default_value(self):
        return date.today()


class TimeType(ComparableType):
    @property
    def native_type(self):
        return time

    @property
    def default_value(self):
        return datetime.now().time()