# -*- coding: utf-8 -*-
from unittest import TestCase
from justamodel.exceptions import ModelValidationError, ValidationError


class TestModelValidationError(TestCase):
    def test_get_or_create_field_get(self):
        a = ModelValidationError()
        a.field_errors['x'] = 'y'
        self.assertEqual(a.get_or_create_field('x'), 'y')

    def test_get_or_create_field_create(self):
        a = ModelValidationError()
        self.assertIsInstance(a.get_or_create_field('x'), ModelValidationError)

    def test_add_field_error(self):
        a = ModelValidationError()
        err = ValidationError('x is invalid')
        a.add_field_error('x', err)
        self.assertEqual(a.field_errors['x'].errors, [err])

    def test_add_field_error_multiple(self):
        a = ModelValidationError()
        err = ValidationError('x is invalid')
        err2 = ValidationError('x is invalid again')
        a.add_field_error('x', err)
        a.add_field_error('x', err2)
        self.assertEqual(a.field_errors['x'].errors, [err, err2])

    def test_add_field_error_model_errors(self):
        a = ModelValidationError()
        err = ModelValidationError()
        err2 = ModelValidationError()
        a.add_field_error('x', err)
        with self.assertRaises(TypeError):
            a.add_field_error('x', err2)

    def test_add_path_error(self):
        a = ModelValidationError()
        err = ValidationError('err')
        err2 = ValidationError('err2')
        err3 = ValidationError('err3')
        err4 = ValidationError('err4')
        a.add_path_error('', err)
        a.add_path_error('test', err2)
        a.add_path_error('test.aa', err3)
        a.add_path_error('test2.test', err4)
        self.assertEqual(a.errors, [err])
        self.assertEqual(a.field_errors['test'].errors, [err2])
        self.assertEqual(a.field_errors['test'].field_errors['aa'].errors, [err3])
        self.assertEqual(a.field_errors['test2'].field_errors['test'].errors, [err4])

    def test_get_errors(self):
        a = ModelValidationError()
        err = ValidationError('err')
        err2 = ValidationError('err2')
        err3 = ValidationError('err3')
        err4 = ValidationError('err4')
        a.add_path_error('', err)
        a.add_path_error('test', err2)
        a.add_path_error('test.aa', err3)
        a.add_path_error('test2.test', err4)
        self.assertEqual(a.get_errors(''), [err])
        self.assertEqual(a.get_errors('test'), [err2])
        self.assertEqual(a.get_errors('test.aa'), [err3])
        self.assertEqual(a.get_errors('test2.test'), [err4])
        self.assertEqual(a.get_errors('test2.test3'), [])
        self.assertEqual(a.get_errors('test2.test3.eee'), [])

    def test_for_field(self):
        err = ValidationError('err')
        a = ModelValidationError.for_field('', err)
        self.assertIsInstance(a, ModelValidationError)
        self.assertEqual(a.errors, [err])