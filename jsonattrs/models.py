from collections import OrderedDict
import re

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField
from django.db.models import (
    BooleanField,
    CharField,
    CommaSeparatedIntegerField,
    DateField,
    DateTimeField,
    DecimalField,
    EmailField,
    FloatField,
    NullBooleanField,
    SlugField,
    TimeField,
    URLField,
    BigIntegerField,
    IntegerField,
    PositiveIntegerField,
    PositiveSmallIntegerField,
    SmallIntegerField
)


class SchemaManager(models.Manager):
    cache = dict()
    content_type_to_selectors = dict()

    @classmethod
    def invalidate_cache(cls):
        cls.cache = dict()

    def lookup(self, instance=None, content_type=None, selectors=None):
        if instance is not None and content_type is None:
            content_type = ContentType.objects.get_for_model(instance)

        if selectors is None and instance is not None:
            # Lazily pre-process per-content type selector definitions.
            if len(self.content_type_to_selectors) == 0:
                for k, v in settings.JSONATTRS_SCHEMA_SELECTORS.items():
                    a, m = k.split('.')
                    self.content_type_to_selectors[
                        ContentType.objects.get(app_label=a, model=m)
                    ] = v

            # Build full list of selectors from instance.
            selectors = []
            for s in self.content_type_to_selectors[content_type]:
                selector = instance
                for step in s.split('.'):
                    selector = getattr(selector, step, None)
                selectors.append(str(selector))
        selectors = tuple(selectors)

        # Look for schema list in cache, keyed by content type and
        # selector list.
        key = (content_type, selectors)
        if key in self.cache:
            return self.cache[key]

        # Not in cache: build schema list using increasing selector
        # sequences.
        base_schemas = self.filter(content_type=content_type)
        schemas = []
        for i in range(len(selectors) + 1):
            schemas += list(base_schemas.filter(selectors=selectors[:i]))
        self.cache[key] = schemas
        return schemas

    def from_instance(self, instance):
        return self.lookup(instance=instance)


class Schema(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    selectors = ArrayField(models.CharField(max_length=256, blank=True),
                           default=list, blank=True)

    class Meta:
        unique_together = ('content_type', 'selectors')

    def __str__(self):
        return '<Schema #{}: {}+{}>'.format(
            self.id,
            self.content_type if self.content_type_id is not None else 'None',
            self.selectors
        )

    def __repr__(self):
        return str(self)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        SchemaManager.invalidate_cache()

    objects = SchemaManager()


def compose_schemas(*schemas):
    # Extract schema attributes, names of required attributes and
    # names of attributes with defaults, composing schemas.
    sattrs = [s.attributes.all() for s in schemas]
    attrs = OrderedDict()
    for sas in sattrs:
        for sa in sas:
            if sa.omit:
                if sa.name in attrs:
                    del attrs[sa.name]
            else:
                attrs[sa.name] = sa
    required_attrs = {n for n, a in attrs.items() if a.required}
    default_attrs = {n for n, a in attrs.items() if a.default is not None}

    return attrs, required_attrs, default_attrs


DEFAULT_FIELD_TYPES = [
    BooleanField,
    CharField,
    CommaSeparatedIntegerField,
    DateField,
    DateTimeField,
    DecimalField,
    EmailField,
    FloatField,
    NullBooleanField,
    SlugField,
    TimeField,
    URLField,
    BigIntegerField,
    IntegerField,
    PositiveIntegerField,
    PositiveSmallIntegerField,
    SmallIntegerField
]
FIELD_TYPES = {f.__name__: f for f in DEFAULT_FIELD_TYPES}
FIELD_TYPE_CHOICES = [(k, k) for k in FIELD_TYPES.keys()]


# TODO: function to add custom field types?


ATTRIBUTE_VALIDATORS = {}


def validator(type, check_valid):
    if not isinstance(type, tuple):
        type = (type, '')
    ATTRIBUTE_VALIDATORS[type] = check_valid


def re_validate(re):
    return lambda v: re.match(v) is not None


int_re = re.compile(r'[-+]?\d+')
pint_re = re.compile(r'\d+')
csint_re = re.compile(r'([-+]?\d+)(,[-+]?\d+)*')
decimal_re = re.compile(r'[-+]?\d+(\.\d+)?')
bool_re = re.compile(r'true|false|True|False')

validator('BigIntegerField', re_validate(int_re))
validator('IntegerField', re_validate(int_re))
validator('SmallIntegerField', re_validate(int_re))
validator('PositiveIntegerField', re_validate(pint_re))
validator('PositiveSmallIntegerField', re_validate(pint_re))
validator('BooleanField', lambda v: (isinstance(v, bool) or
                                     re_validate(bool_re)(v)))
validator('CharField', lambda v: isinstance(v, str))
validator('CommaSeparatedIntegerField', re_validate(csint_re))


# TODO: fill in more validators here.


class Attribute(models.Model):
    schema = models.ForeignKey(
        Schema, related_name='attributes', on_delete=models.CASCADE
    )
    name = models.CharField(max_length=50)
    long_name = models.CharField(max_length=50, blank=True)
    coarse_type = models.CharField(max_length=255, choices=FIELD_TYPE_CHOICES)
    subtype = models.CharField(max_length=255, blank=True)
    index = models.IntegerField()
    choices = models.CharField(max_length=200, blank=True)
    default = models.CharField(max_length=50, blank=True)
    required = models.BooleanField(default=False)
    omit = models.BooleanField(default=False)

    class Meta:
        ordering = ('schema', 'index')
        unique_together = (('schema', 'index'), ('schema', 'name'))

    def validate(self, value):
        if self.choices is not None and self.choices != '':
            if value not in self.choices.split(','):
                raise ValidationError(
                    _('Invalid choice for %(field)s: "%(value)s"'),
                    params={'field': self.name, 'value': value}
                )
        if (self.coarse_type, self.subtype) in ATTRIBUTE_VALIDATORS:
            check = ATTRIBUTE_VALIDATORS[(self.coarse_type, self.subtype)]
            if not check(value):
                raise ValidationError(
                    _('Validation failed for %(field)s: "%(value)s"'),
                    params={'field': self.name, 'value': value}
                )
