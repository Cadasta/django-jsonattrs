from collections import UserDict
# import json

from psycopg2.extras import Json

# from django.core import exceptions
from django.utils.translation import ugettext_lazy as _
from django.contrib.postgres.fields import JSONField

from .models import Schema, compose_schemas


class JSONAttributes(UserDict):
    def __init__(self, *args, **kwargs):
        self._schemas = None
        self._instance = None
        super().__init__(*args, **kwargs)

    def setup_from_dict(self, dict):
        self.setup_schema()
        if dict is not None:
            for k, v in dict.items():
                self._check_key(k)
                self._attrs[k].validate(v)
                self[k] = v

    def setup_schema(self):
        # Determine schemas for model instance containing this field.
        self._schemas = Schema.objects.from_instance(self._instance)

        # Extract schema attributes, names of required attributes and
        # names of attributes with defaults, composing schemas for
        # instance.
        attrs = compose_schemas(*self._schemas)
        self._attrs, self._required_attrs, self._default_attrs = attrs

        # Fill in defaulted attributes.
        if len(self._required_attrs) > 0:
            for key in self._required_attrs:
                self[key] = self._attrs[key].default

    def _check_key(self, key):
        if key not in self._attrs:
            raise KeyError(key)

    def __getitem__(self, key):
        self._check_key(key)
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        self._check_key(key)
        self._attrs[key].validate(value)
        return super().__setitem__(key, value)

    def __delitem__(self, key):
        self._check_key(key)
        if key in self._required_attrs:
            raise KeyError(key)
        return super().__delitem__(key)

    @property
    def schemas(self):
        return self._schemas

    @property
    def attributes(self):
        return self._attrs


class JSONAttributeField(JSONField):
    description = _('A managed JSON attribute set')

    def __init__(self, *args, **kwargs):
        kwargs['default'] = JSONAttributes
        super().__init__(*args, **kwargs)

    # def to_python(self, value):
    #     return JSONAttributes(value)

    def from_db_value(self, value, expression, connection, context):
        return value

    def get_prep_value(self, value):
        return Json(dict(value)) if value is not None else value

    def get_prep_lookup(self, lookup_type, value):
        if lookup_type in ('has_key', 'has_keys', 'has_any_keys'):
            return value
        return (Json(dict(value)) if isinstance(value, dict)
                else super().get_prep_lookup(lookup_type, value))

    # def validate(self, value, model_instance):
    #     super(JSONField, self).validate(value, model_instance)
    #     try:
    #         json.dumps(dict(value))
    #     except TypeError:
    #         raise exceptions.ValidationError(
    #             self.error_messages['invalid'],
    #             code='invalid',
    #             params={'value': value},
    #         )
