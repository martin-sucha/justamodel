# -*- coding: utf-8 -*-
from unittest import TestCase
from unittest.mock import MagicMock
import re
from datetime import date, datetime, time
from justamodel.exceptions import ValidationError, ModelValidationError
from justamodel.model import Model
from justamodel.types import ValueType, BooleanType, SizedType, ComparableType, StringType, UrlType, IntType, \
    DictType, ListType, ModelType, import_object, DateType, TimeType, DateTimeType, SetType


class TestValueType(TestCase):
    def test_runs_validators(self):
        validator = MagicMock()
        value_type = ValueType(validators=[validator])
        value_type.validate(10)
        validator.assert_called_once_with(10)


class TestBooleanType(TestCase):
    def test_validates_type(self):
        bool_type = BooleanType()
        bool_type.validate(True)
        bool_type.validate(False)
        with self.assertRaises(ValidationError):
            bool_type.validate(10)
        with self.assertRaises(ValidationError):
            bool_type.validate('True')
        with self.assertRaises(ValidationError):
            bool_type.validate(None)

    def test_default_value(self):
        self.assertEqual(False, BooleanType().default_value)


class TestSizedType(TestCase):
    def test_validates_without_constraits(self):
        sized_type = SizedType()
        sized_type.validate([])
        sized_type.validate([1, 2, 3])

    def test_validates_min_length(self):
        sized_type = SizedType(min_length=2)
        with self.assertRaises(ValidationError):
            sized_type.validate([])
        with self.assertRaises(ValidationError):
            sized_type.validate([1])
        with self.assertRaises(ValidationError):
            sized_type.validate([2])
        sized_type.validate([1, 2, 3])

    def test_validates_max_length(self):
        sized_type = SizedType(max_length=2)
        sized_type.validate([])
        sized_type.validate([1])
        sized_type.validate([2])
        with self.assertRaises(ValidationError):
            sized_type.validate([1, 2, 3])


class TestComparableType(TestCase):
    def test_validates_without_constraits(self):
        comp_type = ComparableType()
        comp_type.validate(1)
        comp_type.validate(0)

    def test_validates_min_value(self):
        comp_type = ComparableType(min_value=2)
        with self.assertRaises(ValidationError):
            comp_type.validate(0)
        with self.assertRaises(ValidationError):
            comp_type.validate(1)
        comp_type.validate(2)

    def test_validates_max_value(self):
        comp_type = ComparableType(max_value=2)
        comp_type.validate(0)
        comp_type.validate(1)
        comp_type.validate(2)
        with self.assertRaises(ValidationError):
            comp_type.validate(3)
        with self.assertRaises(ValidationError):
            comp_type.validate(4)


class TestStringType(TestCase):
    def test_validates_type(self):
        string_type = StringType()
        string_type.validate('')
        string_type.validate('abc')
        with self.assertRaises(ValidationError):
            string_type.validate(10)
        with self.assertRaises(ValidationError):
            string_type.validate(True)
        with self.assertRaises(ValidationError):
            string_type.validate(None)

    def test_validates_without_constraits(self):
        string_type = StringType()
        string_type.validate('')
        string_type.validate('a string')

    def test_validates_min_length(self):
        string_type = StringType(min_length=2)
        with self.assertRaises(ValidationError):
            string_type.validate('')
        with self.assertRaises(ValidationError):
            string_type.validate('a')
        string_type.validate('ab')

    def test_validates_max_length(self):
        string_type = StringType(max_length=2)
        string_type.validate('')
        string_type.validate('a')
        string_type.validate('ab')
        with self.assertRaises(ValidationError):
            string_type.validate('abc')

    def test_validates_regex(self):
        string_type = StringType(regex='@')
        string_type.validate('@')
        string_type.validate('me@home')
        with self.assertRaises(ValidationError):
            string_type.validate('')
        with self.assertRaises(ValidationError):
            string_type.validate('nothing')

    def test_validates_compiled_regex(self):
        string_type = StringType(regex=re.compile('@'))
        string_type.validate('@')
        string_type.validate('me@home')
        with self.assertRaises(ValidationError):
            string_type.validate('')
        with self.assertRaises(ValidationError):
            string_type.validate('nothing')

    def test_default_value(self):
        self.assertEqual('', StringType().default_value)


class TestUrlType(TestCase):
    def test_validates_without_constraints(self):
        url_type = UrlType()
        url_type.validate('')
        url_type.validate('a string')

    def test_validates_single_scheme(self):
        url_type = UrlType(scheme='http')
        url_type.validate('http://abc')
        url_type.validate('http:')
        with self.assertRaises(ValidationError):
            url_type.validate('')
        with self.assertRaises(ValidationError):
            url_type.validate('htt://aaa')
        with self.assertRaises(ValidationError):
            url_type.validate('https://aaa')

    def test_validates_multiple_schemes(self):
        url_type = UrlType(scheme=('http', 'https'))
        url_type.validate('http://abc')
        url_type.validate('http:')
        url_type.validate('https://abc')
        url_type.validate('https:')
        with self.assertRaises(ValidationError):
            url_type.validate('')
        with self.assertRaises(ValidationError):
            url_type.validate('ftp://aaa')

    def test_checks_scheme_parameter(self):
        UrlType()
        UrlType(scheme='abc')
        UrlType(scheme=('abc', 'def'))
        with self.assertRaises(TypeError):
            UrlType(scheme=10)


class TestIntType(TestCase):
    def test_validates_type(self):
        int_type = IntType()
        int_type.validate(0)
        int_type.validate(1)
        int_type.validate(-123)
        with self.assertRaises(ValidationError):
            int_type.validate(10.0)
        with self.assertRaises(ValidationError):
            int_type.validate('10')
        with self.assertRaises(ValidationError):
            int_type.validate(None)

    def test_default_value(self):
        self.assertEqual(0, IntType().default_value)

    def test_validates_min_value(self):
        int_type = IntType(min_value=2)
        with self.assertRaises(ValidationError):
            int_type.validate(0)
        with self.assertRaises(ValidationError):
            int_type.validate(1)
        int_type.validate(2)

    def test_validates_max_value(self):
        int_type = IntType(max_value=2)
        int_type.validate(0)
        int_type.validate(1)
        int_type.validate(2)
        with self.assertRaises(ValidationError):
            int_type.validate(3)
        with self.assertRaises(ValidationError):
            int_type.validate(4)


class TestListType(TestCase):
    def test_validates_type(self):
        list_type = ListType()
        list_type.validate([])
        list_type.validate(['abc', 'def'])
        list_type.validate([0, 1])
        with self.assertRaises(ValidationError):
            list_type.validate(10.0)
        with self.assertRaises(ValidationError):
            list_type.validate('10')
        with self.assertRaises(ValidationError):
            list_type.validate(None)
        with self.assertRaises(ValidationError):
            list_type.validate({})
        with self.assertRaises(ValidationError):
            list_type.validate(tuple())

    def test_validates_item_type(self):
        mock_type = MagicMock()
        list_type = ListType(item_type=mock_type)
        list_type.validate([])
        list_type.validate(['a'])
        mock_type.validate.assert_called_once_with('a')

        mock_type = MagicMock()
        err = ValidationError('Not \'a\'')

        def validator(value):
            if value != 'a':
                raise err

        mock_type.validate.side_effect = validator

        list_type = ListType(item_type=mock_type)
        list_type.validate([])
        with self.assertRaises(ModelValidationError) as mve:
            list_type.validate(['a', 'b'])
        self.assertEqual(mve.exception.sub_errors[1].errors[0], err)

    def test_validates_min_length(self):
        list_type = ListType(min_length=2)
        with self.assertRaises(ValidationError):
            list_type.validate([])
        with self.assertRaises(ValidationError):
            list_type.validate(['a'])
        list_type.validate(['a', 'b'])

    def test_validates_max_length(self):
        list_type = ListType(max_length=2)
        list_type.validate([])
        list_type.validate(['a'])
        list_type.validate(['a', 'b'])
        with self.assertRaises(ValidationError):
            list_type.validate(['a', 'b', 'c'])


class TestSetType(TestCase):
    def test_validates_type(self):
        set_type = SetType()
        set_type.validate(set())
        set_type.validate({'abc', 'def'})
        set_type.validate({0, 1})
        with self.assertRaises(ValidationError):
            set_type.validate(10.0)
        with self.assertRaises(ValidationError):
            set_type.validate('10')
        with self.assertRaises(ValidationError):
            set_type.validate(None)
        with self.assertRaises(ValidationError):
            set_type.validate([])
        with self.assertRaises(ValidationError):
            set_type.validate(tuple())

    def test_validates_item_type(self):
        mock_type = MagicMock()
        set_type = SetType(item_type=mock_type)
        set_type.validate(set())
        set_type.validate({'a'})
        mock_type.validate.assert_called_once_with('a')

        mock_type = MagicMock()
        err = ValidationError('Not \'a\'')

        def validator(value):
            if value != 'a':
                raise err

        mock_type.validate.side_effect = validator

        set_type = SetType(item_type=mock_type)
        set_type.validate(set())
        with self.assertRaises(ModelValidationError) as mve:
            set_type.validate({'a', 'b'})
        self.assertEqual(mve.exception.sub_errors['b'].errors[0], err)

    def test_validates_min_length(self):
        set_type = SetType(min_length=2)
        with self.assertRaises(ValidationError):
            set_type.validate(set())
        with self.assertRaises(ValidationError):
            set_type.validate({'a'})
        set_type.validate({'a', 'b'})

    def test_validates_max_length(self):
        set_type = SetType(max_length=2)
        set_type.validate(set())
        set_type.validate({'a'})
        set_type.validate({'a', 'b'})
        with self.assertRaises(ValidationError):
            set_type.validate({'a', 'b', 'c'})


class TestDictType(TestCase):
    def test_validates_type(self):
        dict_type = DictType()
        dict_type.validate({})
        dict_type.validate({'abc': 'def'})
        dict_type.validate({0: 1})
        with self.assertRaises(ValidationError):
            dict_type.validate(10.0)
        with self.assertRaises(ValidationError):
            dict_type.validate('10')
        with self.assertRaises(ValidationError):
            dict_type.validate(None)

    def test_validates_key_type(self):
        mock_type = MagicMock()
        dict_type = DictType(key_type=mock_type)
        dict_type.validate({})
        dict_type.validate({'a': 'b'})
        mock_type.validate.assert_called_once_with('a')

        mock_type = MagicMock()
        err = ValidationError('Not \'a\'')

        def validator(value):
            if value != 'a':
                raise err

        mock_type.validate.side_effect = validator

        dict_type = DictType(key_type=mock_type)
        dict_type.validate(dict())
        with self.assertRaises(ModelValidationError) as mve:
            dict_type.validate({'a': 'c', 'b': 'd'})
        self.assertEqual(mve.exception.sub_errors['b'].sub_errors['key'].errors[0], err)

    def test_validates_value_type(self):
        mock_type = MagicMock()
        dict_type = DictType(value_type=mock_type)
        dict_type.validate({})
        dict_type.validate({'a': 'b'})
        mock_type.validate.assert_called_once_with('b')

        mock_type = MagicMock()
        err = ValidationError('Not \'a\'')

        def validator(value):
            if value != 'a':
                raise err

        mock_type.validate.side_effect = validator

        dict_type = DictType(value_type=mock_type)
        dict_type.validate(dict())
        with self.assertRaises(ModelValidationError) as mve:
            dict_type.validate({'a': 'c', 'b': 'a'})
        self.assertEqual(mve.exception.sub_errors['a'].sub_errors['value'].errors[0], err)


class TestModelType(TestCase):
    def test_validates_type(self):
        model_type = ModelType(Model)
        model_type.validate(Model())
        with self.assertRaises(ValidationError):
            model_type.validate(10.0)
        with self.assertRaises(ValidationError):
            model_type.validate({'a': 'b'})
        with self.assertRaises(ValidationError):
            model_type.validate(None)

    def test_validates_model(self):
        mock_model = MagicMock(spec=Model)
        model_type = ModelType(Model)
        model_type.validate(mock_model)
        mock_model.validate.assert_called_once_with()

    def test_reference_by_name(self):
        model_type = ModelType('justamodel.model.Model')
        self.assertIs(model_type.model_class, Model)


class TestImportObject(TestCase):
    def test_import_object(self):
        date_type = import_object('justamodel.types.DateType')
        self.assertIs(date_type, DateType)

    def test_import_with_attribute(self):
        date_type_attribute = import_object('justamodel.types.DateType.default_value')
        self.assertIs(date_type_attribute, DateType.default_value)

    def test_import_builtin(self):
        self.assertIs(import_object('range'), range)

    def test_import_nonexistent(self):
        with self.assertRaises(AttributeError):
            import_object('this_does_not_exist')


class TestDateType(TestCase):
    def test_default_value(self):
        self.assertIsInstance(DateType().default_value, DateType().native_type)


class TestDateTimeType(TestCase):
    def test_default_value(self):
        self.assertIsInstance(DateTimeType().default_value, DateTimeType().native_type)


class TestTimeType(TestCase):
    def test_default_value(self):
        self.assertIsInstance(TimeType().default_value, TimeType().native_type)