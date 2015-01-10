from unittest import TestCase
import unittest
from justamodel.exceptions import ValidationError
from justamodel.model import Model, Field, PolymorphicModel
from justamodel.serializer import DictModelSerializer, VerbatimFieldSerializer, JsonModelSerializer, make_field_filter, \
    iter_model_fields
from justamodel.types import StringType, IntType, UrlType, ModelType


class TestModel(Model):
    string_field = Field(StringType())
    int_field = Field(IntType())
    url_field = Field(UrlType(scheme='http'))


class TestModelA(Model):
    a_field = Field(StringType())
    x = Field(IntType())


class TestModelB(Model):
    a_field = Field(IntType())
    y = Field(IntType())


class TestModelAB(PolymorphicModel):
    types_to_model_classes = {
        'a': TestModelA,
        'b': TestModelB
    }


class TestComposedModel(Model):
    name = Field(StringType())
    submodel = Field(ModelType(TestModelA))


class TestComposedModel2(Model):
    name = Field(StringType())
    submodel = Field(ModelType(TestModelA), required=False)


class TestInheritedModel(TestModel):
    another_field = Field(StringType())


class TestDictSerialization(TestCase):
    def setUp(self):
        self.serializer = DictModelSerializer(VerbatimFieldSerializer())

    def test_deserialization(self):
        deserialized = self.serializer.deserialize_model({
            'string_field': 'a string',
            'int_field': 46,
            'url_field': 'http://abc'
        }, TestModel)
        expected = TestModel(string_field='a string', int_field=46, url_field='http://abc')
        self.assertEqual(expected, deserialized)

    def test_deserialization_into_instance(self):
        deserialized = TestModel(int_field=46)
        self.serializer.deserialize_model({
            'string_field': 'a string',
            'url_field': 'http://abc'
        }, deserialized)
        expected = TestModel(string_field='a string', int_field=None, url_field='http://abc')
        self.assertEqual(expected, deserialized)

    def test_deserialization_invalid(self):
        with self.assertRaises(ValidationError):
            self.serializer.deserialize_model(10, TestModel)

    def test_serialization(self):
        serialized = self.serializer.serialize_model(TestModel(string_field='a string', int_field=46, url_field='http://abc'))
        expected = {
            'string_field': 'a string',
            'int_field': 46,
            'url_field': 'http://abc'
        }
        self.assertEqual(expected, serialized)

    def test_serialization_invalid(self):
        with self.assertRaises(TypeError):
            self.serializer.serialize_model(10)

    def test_deserialization_polymorphic(self):
        deserialized = self.serializer.deserialize_model({
            'type': 'a',
            'a_field': 'a_field',
            'x': 10
        }, TestModelAB)
        expected = TestModelA(a_field='a_field', x=10)
        self.assertEqual(expected, deserialized)

        deserialized = self.serializer.deserialize_model({
            'type': 'b',
            'a_field': 20,
            'y': 30
        }, TestModelAB)
        expected = TestModelB(a_field=20, y=30)
        self.assertEqual(expected, deserialized)

    def test_deserialization_polymorphic_invalid(self):
        with self.assertRaises(ValidationError):
            self.serializer.deserialize_model({
                'a_field': 'a_field',
                'x': 10
            }, TestModelAB)

    def test_serialization_polymorphic(self):
        model = TestModelA(a_field='a string', x=10)
        serialized = self.serializer.serialize_model(model, model_type=TestModelAB)
        expected = {
            'a_field': 'a string',
            'x': 10,
            'type': 'a'
        }
        self.assertEqual(expected, serialized)

        model = TestModelB(a_field=20, y=30)
        serialized = self.serializer.serialize_model(model, model_type=TestModelAB)
        expected = {
            'a_field': 20,
            'y': 30,
            'type': 'b'
        }
        self.assertEqual(expected, serialized)

    def test_deserialization_inherited(self):
        deserialized = self.serializer.deserialize_model({
            'string_field': 'a string',
            'int_field': 46,
            'url_field': 'http://abc',
            'another_field': 'test'
        }, TestInheritedModel)
        expected = TestInheritedModel(string_field='a string', int_field=46, url_field='http://abc',
                                      another_field='test')
        self.assertEqual(expected, deserialized)

    def test_serialization_inherited(self):
        model = TestInheritedModel(string_field='a string', int_field=46, url_field='http://abc', another_field='test')
        serialized = self.serializer.serialize_model(model)
        expected = {
            'string_field': 'a string',
            'int_field': 46,
            'url_field': 'http://abc',
            'another_field': 'test'
        }
        self.assertEqual(expected, serialized)

    def test_serialization_composed(self):
        model = TestComposedModel(name='test', submodel=TestModelA(a_field='abc', x=10))
        serialized = self.serializer.serialize_model(model)
        expected = {
            'name': 'test',
            'submodel': {
                'a_field': 'abc',
                'x': 10
            }
        }
        self.assertEqual(expected, serialized)

    def test_deserialization_composed(self):
        serialized = {
            'name': 'test',
            'submodel': {
                'a_field': 'abc',
                'x': 10
            }
        }
        deserialized = self.serializer.deserialize_model(serialized, TestComposedModel)
        expected = TestComposedModel(name='test', submodel=TestModelA(a_field='abc', x=10))
        self.assertEqual(expected, deserialized)

    def test_serialization_none(self):
        model = TestComposedModel2(name='test', submodel=None)
        serialized = self.serializer.serialize_model(model)
        expected = {
            'name': 'test',
            'submodel': None
        }
        self.assertEqual(expected, serialized)

    def test_deserialization_none(self):
        serialized = {
            'name': 'test',
            'submodel': None
        }
        deserialized = self.serializer.deserialize_model(serialized, TestComposedModel2)
        expected = TestComposedModel2(name='test', submodel=None)
        self.assertEqual(expected, deserialized)


class TestSerializationJson(TestCase):
    def setUp(self):
        self.serializer = JsonModelSerializer(VerbatimFieldSerializer(), sort_keys=True)

    def test_deserialization_json(self):
        deserialized = self.serializer.deserialize_model('''{
            "string_field": "a string",
            "int_field": 46,
            "url_field": "http://abc"
        }''', TestModel)
        expected = TestModel(string_field='a string', int_field=46, url_field='http://abc')
        self.assertEqual(expected, deserialized)

    def test_deserialization_json_invalid(self):
        with self.assertRaises(ValidationError):
            self.serializer.deserialize_model('{invalid json', TestModel)

    def test_serialization_json(self):
        serialized = self.serializer.serialize_model(TestModel(string_field='a string', int_field=46, url_field='http://abc'))
        expected = '{"int_field": 46, "string_field": "a string", "url_field": "http://abc"}'
        self.assertEqual(expected, serialized)


class TestFieldFiltering(TestCase):
    def test_make_filter_none(self):
        f = make_field_filter(None)
        self.assertTrue(f('a'))
        self.assertTrue(f('b'))
        self.assertTrue(f('c'))

    def test_make_filter_list(self):
        f = make_field_filter(['a', 'b'])
        self.assertTrue(f('a'))
        self.assertTrue(f('b'))
        self.assertFalse(f('c'))

    def test_make_filter_lambda(self):
        f = make_field_filter(lambda x: x == 'a' or x == 'c')
        self.assertTrue(f('a'))
        self.assertFalse(f('b'))
        self.assertTrue(f('c'))

    def test_iter_fields_with_filter(self):
        fields = list(iter_model_fields(TestModel, fields=['url_field', 'string_field']))
        self.assertEqual(fields, [('string_field', TestModel.fields['string_field']),
                                  ('url_field', TestModel.fields['url_field']),
                                  ])

    def test_iter_fields_without_filter(self):
        fields = list(iter_model_fields(TestModel))
        self.assertEqual(fields, [('string_field', TestModel.fields['string_field']),
                                  ('int_field', TestModel.fields['int_field']),
                                  ('url_field', TestModel.fields['url_field']),
                                  ])
