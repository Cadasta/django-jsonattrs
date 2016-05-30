import re

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField

from .settings import FIELD_TYPES


class SchemaManager(models.Manager):
    def from_instance(self, instance):
        base_schemas = self.filter(
            content_type=ContentType.objects.get_for_model(instance)
        )
        selectors = ()
        schemas = list(base_schemas.filter(selectors=()))
        for s in settings.JSONATTRS_SCHEMA_SELECTORS:
            selector = instance
            for step in s.split('.'):
                selector = getattr(selector, step, None)
            selectors = selectors + (selector,)
            schemas += list(base_schemas.filter(selectors=selectors))
        return schemas


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

    objects = SchemaManager()


FIELD_TYPE_CHOICES = [(field, field) for field in FIELD_TYPES]


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
