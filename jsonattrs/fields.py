from collections import UserDict
import json
from datetime import date, datetime

from psycopg2.extras import Json

# from django.core import exceptions
from django.utils.translation import ugettext_lazy as _
from django.contrib.postgres.fields import JSONField

from .models import Schema, compose_schemas


class JSONAttributes(UserDict):
    def __init__(self, *args, **kwargs):
        self._schemas = None
        self._instance = None
        self._setup = False
        super().__init__(*args, **kwargs)

    def setup_from_dict(self, dict):
        self.setup_schema()
        if dict is None or len(dict) == 0:
            self._setup = False
        else:
            for k, v in dict.items():
                self._check_key(k)
                self._attrs[k].validate(v)
                self[k] = v

    def setup_schema(self, schemas=None):
        if self._setup and schemas is None:
            return

        # Determine schemas for model instance containing this field.
        if schemas is not None:
            self._schemas = schemas
        else:
            self._schemas = Schema.objects.from_instance(self._instance)
        self._setup = True

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
        self.setup_schema()
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
        self.setup_schema()
        return self._schemas

    @property
    def attributes(self):
        self.setup_schema()
        return self._attrs


# This is needed to provide JSON serialisation for date objects
# whenever they're saved to JSON attribute fields.  This function is
# passed as the custom "dumps" method for psycopg2's Json class to
# use.

def json_serialiser(obj):
    return json.dumps(
        obj,
        default=lambda obj: (
            obj.isoformat()
            if isinstance(obj, datetime) or isinstance(obj, date)
            else None
        )
    )


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
        return (Json(dict(value), dumps=json_serialiser)
                if value is not None else value)

    def get_prep_lookup(self, lookup_type, value):
        if lookup_type in ('has_key', 'has_keys', 'has_any_keys'):
            return value
        return (Json(dict(value), dumps=json_serialiser)
                if isinstance(value, dict)
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
