from collections import UserDict, OrderedDict
# import json

# from psycopg2.extras import Json

# from django.core import exceptions
# from django.utils.translation import ugettext_lazy as _
from django.contrib.postgres.fields import JSONField


class JSONAttributes(UserDict):
    def __init__(self, schema, *args, **kwargs):
        self._schema = schema

        # Extract schema attributes, names of required attributes and
        # names of attributes with defaults.
        sattrs = schema.attributes.all()
        self._attrs = OrderedDict((a.name, a) for a in sattrs)
        self._required_attrs = {a.name for a in sattrs if a.required}
        self._default_attrs = {a.name for a in sattrs if a.default is not None}

        # Check for presence of all required attributes in kwargs.
        for key in self._required_attrs:
            if key not in kwargs:
                raise KeyError(key)

        # Validate all kwargs.
        for name, value in kwargs.items():
            self._attrs[name].validate(value)

        # Add defaulted fields to kwargs
        for key in self._default_attrs:
            if key not in kwargs:
                kwargs[key] = self._attrs[key].default

        super().__init__(*args, **kwargs)

    def _check_key(self, key):
        if key not in self._attrs:
            raise KeyError(key)

    def __getitem__(self, key):
        self._check_key(key)
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        self._check_key(key)
        return super().__setitem__(key, value)

    def __delitem__(self, key):
        self._check_key(key)
        return super().__delitem__(key)

    @property
    def schema(self):
        return self._schema

    @property
    def attributes(self):
        return self._attrs


class JSONAttributeField(JSONField):
    pass

    # description = _('A managed JSON attribute set')

    # # Needs method to:
    # #  - Get model object
    # #  - Get model fields based on JSONATTRS_SCHEMA_SELECTORS
    # #  - Build selector tuple
    # #  - Look up schema

    # def to_python(self, value):
    #     return JSONAttributes(value)

    # def get_prep_value(self, value):
    #     if value is not None:
    #         return Json(dict(value))
    #     return value

    # def get_prep_lookup(self, lookup_type, value):
    #     if lookup_type in ('has_key', 'has_keys', 'has_any_keys'):
    #         return value
    #     return Json(dict(value))

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
