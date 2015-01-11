# -*- coding: utf-8 -*-


class ValidationError(ValueError):
    pass


class ModelValidationError(ValidationError):
    def __init__(self, *args, **kwargs):
        super().__init__('Model validation failed', *args, **kwargs)
        self.errors = []
        self.sub_errors = {}

    def add_error(self, error):
        self.errors.append(error)

    def get_or_create_field(self, name):
        if name in self.sub_errors:
            field_errors = self.sub_errors[name]
        else:
            field_errors = ModelValidationError()
            self.sub_errors[name] = field_errors
        return field_errors

    def add_sub_error(self, name, error):
        if isinstance(error, ModelValidationError):
            if name in self.sub_errors:
                raise TypeError('Merging multiple model validation errors is not supported')
            self.sub_errors[name] = error
            return

        self.get_or_create_field(name).add_error(error)

    def add_path_error(self, error, *path):
        if not path:
            return self.add_error(error)

        cur = self
        for part in path[:-1]:
            cur = cur.get_or_create_field(part)

        cur.add_sub_error(path[-1], error)

    @classmethod
    def for_path(cls, error, *path):
        wrapped_error = cls()
        wrapped_error.add_path_error(error, *path)
        return wrapped_error

    def get_errors(self, *path):
        if not path:
            return self.errors

        cur = self
        for part in path:
            if part not in cur.sub_errors:
                return []

            cur = cur.sub_errors[part]

        return cur.errors

    def __bool__(self):
        return bool(self.errors) or bool(self.sub_errors)