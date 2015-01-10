# -*- coding: utf-8 -*-
from unittest import TestCase
from unittest.mock import MagicMock
from justamodel.exceptions import ValidationError, ModelValidationError
from justamodel.model import Field, Model, PolymorphicModel, get_model_class_for_type, get_type_name_for_model, \
    get_type_specifier_name


class TestField(TestCase):
    def test_sets_init_attributes(self):
        field = Field(MagicMock(), custom='hello')
        self.assertEqual('hello', field.custom)

    def test_repr(self):
        field_type = MagicMock()
        field_type.__repr__ = MagicMock()
        field_type.__repr__.return_value = 'MockType'

        field = Field(field_type, custom='hello')
        self.assertEqual('Field(MockType, required=True, default=type_default, custom=\'hello\')', repr(field))

        field = Field(field_type, custom='hello', default='abc', required=False)
        self.assertEqual('Field(MockType, required=False, default=\'abc\', custom=\'hello\')', repr(field))

    def test_creates_default_value_from_type(self):
        mock_type = MagicMock()
        mock_type.default_value = 10
        field = Field(mock_type)
        self.assertEqual(10, field.create_default_value())

    def test_creates_default_value_literal(self):
        field = Field(MagicMock(), default=10)
        self.assertEqual(10, field.create_default_value())

    def test_creates_default_value_callable(self):
        field = Field(MagicMock(), default=lambda: 10)
        self.assertEqual(10, field.create_default_value())

    def test_creates_default_value_if_not_required(self):
        field = Field(MagicMock(), required=False)
        self.assertIsNone(field.create_default_value())

    def test_validates_required(self):
        mock_type = MagicMock()
        field = Field(mock_type, required=True)
        field.validate(10)
        with self.assertRaises(ValidationError):
            field.validate(None)

    def test_validates_type_if_value(self):
        mock_type = MagicMock()
        field = Field(mock_type)
        field.validate(10)
        mock_type.validate.assert_called_once_with(10)

    def test_does_not_validate_type_if_no_value(self):
        mock_type = MagicMock()
        field = Field(mock_type, required=False)
        field.validate(None)
        self.assertEqual(0, mock_type.validate.call_count)


class TestModelMeta(TestCase):
    def test_copies_fields(self):
        field = Field(MagicMock())

        class TestModel(Model):
            a = field

        self.assertEqual(TestModel.fields, {'a': field})

    def test_copies_inherited_fields(self):
        base_field = Field(MagicMock())
        overriden_field = Field(MagicMock(), required=False)
        another_field = Field(MagicMock())

        class BaseModel(Model):
            field = base_field

        class OverridingModel(BaseModel):
            field = overriden_field

        class InheritingModel(OverridingModel):
            another = another_field

        self.assertEqual(InheritingModel.fields, {'field': overriden_field, 'another': another_field})


class TestModel(TestCase):
    def test_setting_default_in_constructor(self):
        mock_field = MagicMock(spec=Field)
        mock_field.create_default_value = MagicMock(return_value=10)

        class TestModel(Model):
            a = mock_field

        self.assertEqual(10, TestModel().a)
        self.assertEqual(1, mock_field.create_default_value.call_count)

        mock_field.reset_mock()
        self.assertEqual(20, TestModel(a=20).a)
        self.assertEqual(0, mock_field.create_default_value.call_count)

    def test_equals(self):
        class TestModel(Model):
            a = Field(MagicMock())
            b = Field(MagicMock(), default='abc')

        class TestSubModel(TestModel):
            pass

        self.assertTrue(TestModel(a='123') == TestModel(a='123'))
        self.assertTrue(TestModel(a='123', b='def') == TestModel(a='123', b='def'))
        self.assertFalse(TestModel(a='134') == TestModel(a='123'))
        self.assertFalse(TestModel(a='123', b='def') == TestModel(a='123', b='deg'))
        self.assertFalse(TestSubModel(a='123') == TestModel(a='123'))
        self.assertFalse(TestModel(a='123') == TestSubModel(a='123'))

    def test_not_equals(self):
        class TestModel(Model):
            a = Field(MagicMock())
            b = Field(MagicMock(), default='abc')

        class TestSubModel(TestModel):
            pass

        self.assertFalse(TestModel(a='123') != TestModel(a='123'))
        self.assertFalse(TestModel(a='123', b='def') != TestModel(a='123', b='def'))
        self.assertTrue(TestModel(a='134') != TestModel(a='123'))
        self.assertTrue(TestModel(a='123', b='def') != TestModel(a='123', b='deg'))
        self.assertTrue(TestSubModel(a='123') != TestModel(a='123'))
        self.assertTrue(TestModel(a='123') != TestSubModel(a='123'))

    def test_validate_valid(self):
        type_mock_a = MagicMock()
        type_mock_b = MagicMock()

        class TestModel(Model):
            a = Field(type_mock_a)
            b = Field(type_mock_b)

        TestModel(a=5, b=10).validate()

        type_mock_a.validate.assert_called_once_with(5)
        type_mock_b.validate.assert_called_once_with(10)

    def test_validate_invalid(self):
        type_mock_a = MagicMock()
        error_a = ValidationError('Invalid value A')
        type_mock_a.validate = MagicMock(side_effect=error_a)
        type_mock_b = MagicMock()
        error_b = ValidationError('Invalid value B')
        type_mock_b.validate = MagicMock(side_effect=error_b)

        class TestModel(Model):
            a = Field(type_mock_a)
            b = Field(type_mock_b)

        with self.assertRaises(ValidationError) as e:
            TestModel(a=5, b=10).validate()

        type_mock_a.validate.assert_called_once_with(5)
        type_mock_b.validate.assert_called_once_with(10)

        self.assertEqual(e.exception.sub_errors['a'].errors, [error_a])
        self.assertEqual(e.exception.sub_errors['b'].errors, [error_b])


class TestPolymorphicModel(TestCase):
    def setUp(self):
        class TestModelA(Model):
            a = MagicMock()

        class TestModelB(Model):
            b = MagicMock()

        class TestModelC(TestModelB):
            c = MagicMock()

        class PolymorphicTestModel(PolymorphicModel):
            types_to_model_classes = {
                'a': TestModelA,
                'b': TestModelB,
                'c': TestModelC
            }

        self.test_type_a = TestModelA
        self.test_type_b = TestModelB
        self.test_type_c = TestModelC
        self.test_type = PolymorphicTestModel

    def test_get_model_type_for_class(self):
        self.assertEqual('a', self.test_type.get_model_type_for_class(self.test_type_a))
        self.assertEqual('b', self.test_type.get_model_type_for_class(self.test_type_b))
        self.assertEqual('c', self.test_type.get_model_type_for_class(self.test_type_c))
        self.assertIsNone(self.test_type.get_model_type_for_class(Model))

    def test_get_model_class_for_type(self):
        self.assertIs(self.test_type_a, self.test_type.get_model_class_for_type('a'))
        self.assertIs(self.test_type_b, self.test_type.get_model_class_for_type('b'))
        self.assertIs(self.test_type_c, self.test_type.get_model_class_for_type('c'))

    def test_subclass_check(self):
        self.assertTrue(issubclass(self.test_type_a, self.test_type))
        self.assertTrue(issubclass(self.test_type_b, self.test_type))
        self.assertTrue(issubclass(self.test_type_c, self.test_type))
        self.assertFalse(issubclass(Model, self.test_type))

    def test_cannot_be_inherited(self):
        class MyModel(PolymorphicModel):
            types_to_model_classes = {}

        with self.assertRaises(TypeError):
            class Inherited(MyModel):
                pass

    def test_factory(self):
        class MyModel(PolymorphicModel):
            types_to_model_classes = {
                'a': Model
            }

        self.assertIsInstance(MyModel('a'), Model)
        with self.assertRaises(ValueError):
            MyModel('x')


class TestGlobals(TestCase):
    def test_get_model_class_for_type(self):
        self.assertIs(Model, get_model_class_for_type(Model, None))

        class Polymorphic(PolymorphicModel):
            types_to_model_classes = {
                'a': Model
            }

        self.assertIs(Model, get_model_class_for_type(Polymorphic, 'a'))
        with self.assertRaises(ValidationError):
            get_model_class_for_type(Polymorphic, 'b')

    def test_get_model_type_for_class(self):
        class Polymorphic(PolymorphicModel):
            types_to_model_classes = {
                'a': Model
            }

        self.assertEquals('a', get_type_name_for_model(Polymorphic, Model))
        with self.assertRaises(TypeError):
            get_type_name_for_model(Polymorphic, object)

    def test_get_type_specifier_name_model(self):
        self.assertIsNone(get_type_specifier_name(Model))

    def test_get_type_specifier_name_polymorphic(self):
        class Polymorphic(PolymorphicModel):
            types_to_model_classes = {
                'a': Model
            }

        self.assertEqual('type', get_type_specifier_name(Polymorphic))

        class Polymorphic2(PolymorphicModel):
            types_to_model_classes = {
                'a': Model
            }
            type_specifier_name = 'another_type'

        self.assertEqual('another_type', get_type_specifier_name(Polymorphic2))
