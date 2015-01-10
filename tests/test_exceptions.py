# -*- coding: utf-8 -*-
from unittest import TestCase
from justamodel.exceptions import ModelValidationError, ValidationError


class TestModelValidationError(TestCase):
    def test_get_or_create_field_get(self):
        a = ModelValidationError()
        a.sub_errors['x'] = 'y'
        self.assertEqual(a.get_or_create_field('x'), 'y')

    def test_get_or_create_field_create(self):
        a = ModelValidationError()
        self.assertIsInstance(a.get_or_create_field('x'), ModelValidationError)

    def test_add_field_error(self):
        a = ModelValidationError()
        err = ValidationError('x is invalid')
        a.add_sub_error('x', err)
        self.assertEqual(a.sub_errors['x'].errors, [err])

    def test_add_field_error_multiple(self):
        a = ModelValidationError()
        err = ValidationError('x is invalid')
        err2 = ValidationError('x is invalid again')
        a.add_sub_error('x', err)
        a.add_sub_error('x', err2)
        self.assertEqual(a.sub_errors['x'].errors, [err, err2])

    def test_add_field_error_model_errors(self):
        a = ModelValidationError()
        err = ModelValidationError()
        err2 = ModelValidationError()
        a.add_sub_error('x', err)
        with self.assertRaises(TypeError):
            a.add_sub_error('x', err2)

    def _nested_errors(self):
        a = ModelValidationError()
        err = ValidationError('err')
        err2 = ValidationError('err2')
        err3 = ValidationError('err3')
        err4 = ValidationError('err4')
        err5 = ValidationError('err5')
        err6 = ValidationError('err6')
        a.add_path_error(err)
        a.add_path_error(err2, 'test')
        a.add_path_error(err3, 'test', 'aa')
        a.add_path_error(err4, 'test2', 'test')
        a.add_path_error(err5, 'test2', 0)
        a.add_path_error(err6, 'test2.test')
        return a, err, err2, err3, err4, err5, err6

    def test_add_path_error(self):
        a, err, err2, err3, err4, err5, err6 = self._nested_errors()
        self.assertEqual(a.errors, [err])
        self.assertEqual(a.sub_errors['test'].errors, [err2])
        self.assertEqual(a.sub_errors['test'].sub_errors['aa'].errors, [err3])
        self.assertEqual(a.sub_errors['test2'].sub_errors['test'].errors, [err4])
        self.assertEqual(a.sub_errors['test2'].sub_errors[0].errors, [err5])
        self.assertEqual(a.sub_errors['test2.test'].errors, [err6])

    def test_get_errors(self):
        a, err, err2, err3, err4, err5, err6 = self._nested_errors()
        self.assertEqual(a.get_errors(), [err])
        self.assertEqual(a.get_errors('test'), [err2])
        self.assertEqual(a.get_errors('test', 'aa'), [err3])
        self.assertEqual(a.get_errors('test2', 'test'), [err4])
        self.assertEqual(a.get_errors('test2', 0), [err5])
        self.assertEqual(a.get_errors('test2.test'), [err6])
        self.assertEqual(a.get_errors('test2', 'test3'), [])
        self.assertEqual(a.get_errors('test2', 'test3', 'eee'), [])

    def test_for_path(self):
        err = ValidationError('err')
        a = ModelValidationError.for_path(err)
        self.assertIsInstance(a, ModelValidationError)
        self.assertEqual(a.errors, [err])