# -*- coding: utf-8 -*-


class ValidationError(Exception):
    pass


class ModelValidationError(ValidationError):
    def __init__(self, *args, **kwargs):
        super().__init__('Model validation failed', *args, **kwargs)
        self.errors = []
        self.field_errors = {}

    def add_error(self, error):
        self.errors.append(error)

    def get_or_create_field(self, name):
        if name in self.field_errors:
            field_errors = self.field_errors[name]
        else:
            field_errors = ModelValidationError()
            self.field_errors[name] = field_errors
        return field_errors

    def add_field_error(self, name, error):
        if isinstance(error, ModelValidationError):
            if name in self.field_errors:
                raise TypeError('Merging multiple model validation errors is not supported')
            self.field_errors[name] = error
            return

        self.get_or_create_field(name).add_error(error)

    def add_path_error(self, path, error):
        if not path:
            return self.add_error(error)

        spath = path.split('.')
        cur = self
        for part in spath[:-1]:
            cur = cur.get_or_create_field(part)

        cur.add_field_error(spath[-1], error)

    @classmethod
    def for_field(cls, path, error):
        wrapped_error = cls()
        wrapped_error.add_path_error(path, error)
        return wrapped_error

    def get_errors(self, path=''):
        if not path:
            return self.errors

        cur = self
        for part in path.split('.'):
            if part not in cur.field_errors:
                return []

            cur = cur.field_errors[part]

        return cur.errors

    def __bool__(self):
        return bool(self.errors) or bool(self.field_errors)