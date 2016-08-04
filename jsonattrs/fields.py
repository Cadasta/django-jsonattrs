from collections import UserDict
import json
from datetime import date, datetime

from psycopg2.extras import Json

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.contrib.postgres.fields import JSONField

from .models import Schema, compose_schemas
from .exceptions import SchemaUpdateConflict, SchemaUpdateException


class JSONAttributes(UserDict):
    def __init__(self, *args, **kwargs):
        self._schemas = None
        self._instance = None
        self._setup = False
        self._saved_selectors = None
        super().__init__(*args, **kwargs)

    def setup_from_dict(self, dict):
        self.setup_schema()
        if dict is None or len(dict) == 0:
            self._setup = False
        else:
            self._check_required_keys(dict.keys())
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
                if (self._attrs[key].default is not None and
                   self._attrs[key].default != ''):
                    self[key] = self._attrs[key].default

    def _pre_save_selector_check(self, strict=False):
        old_selectors = self._saved_selectors
        new_selectors = Schema.objects._get_selectors(self._instance)
        self._saved_selectors = new_selectors
        if (old_selectors is None or
           not any([n != o for n, o in zip(old_selectors, new_selectors)])):
            return
        self._setup = False
        schemas_s = self._schemas
        attrs_s = self._attrs
        required_attrs_s = self._required_attrs
        default_attrs_s = self._default_attrs
        self.setup_schema()
        conflicts = self._attr_list_conflicts(attrs_s, self._attrs,
                                              strict=strict)
        if conflicts is not None and len(conflicts) > 0:
            self._schemas = schemas_s
            self._attrs = attrs_s
            self._required_attrs = required_attrs_s
            self._default_attrs = default_attrs_s
            raise SchemaUpdateException(conflicts=conflicts)

    def _attr_list_conflicts(self, old_attrs, new_attrs, strict=False):
        conflicts = []
        for aname, a in new_attrs.items():
            val = super().get(aname, None)
            if aname not in old_attrs:
                if a.required and (a.default is None or len(a.default) == 0):
                    conflicts.append(
                        SchemaUpdateConflict(aname, 'required_no_default')
                    )
            else:
                olda = old_attrs[aname]
                if not types_compatible(a.attr_type, olda.attr_type, val):
                    conflicts.append(
                        SchemaUpdateConflict(aname, 'incompatible_type')
                    )
                if (strict and
                   not choices_compatible(a.choices, olda.choices, val)):
                    conflicts.append(
                        SchemaUpdateConflict(aname, 'incompatible_choices')
                    )
        return conflicts

    def _check_required_keys(self, keys):
        for req in self._required_attrs:
            if req not in keys and req not in self._default_attrs:
                raise ValidationError(
                    _('Missing required field %(field)s'),
                    params={'field': req}
                )

    def _check_key(self, key):
        self.setup_schema()
        if key not in self._attrs and key not in self:
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


def types_compatible(new_type, old_type, value):
    return (new_type == old_type or
            new_type.name == 'text' or new_type.name == 'text_multiline')


def choices_compatible(new_choices, old_choices, value):
    return new_choices is None or len(new_choices) == 0 or value in new_choices


def schema_update_conflicts(instance):
    if not hasattr(instance, '_attr_field'):
        raise ValueError("instance doesn't have an attribute field")
    conflicts = []
    try:
        instance._attr_field._pre_save_selector_check(strict=True)
    except SchemaUpdateException as exc_info:
        conflicts = exc_info.conflicts
    return conflicts


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
        if value is None:
            return None
        return Json(dict(value), dumps=json_serialiser)

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
