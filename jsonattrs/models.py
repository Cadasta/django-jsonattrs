import re
from itertools import groupby, count

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from .settings import FIELD_TYPES


class SchemaManager(models.Manager):
    def create(self, content_type, selectors=()):
        schema = super().create(content_type=content_type)
        for selector, index in zip(selectors, count(1)):
            SchemaSelector.objects.create(
                schema=schema, index=index, selector=selector
            )
        return schema

    def by_selectors(self, content_type, selectors=()):
        # Find possible matching schemata based on content type.
        schemata = Schema.objects.filter(content_type=content_type)

        # Retrieve schema selectors for these schemata, grouping by
        # schema (they'll be returned in index order).
        grouped = [(k, tuple(ss.selector for ss in g))
                   for k, g
                   in groupby(
                       SchemaSelector.objects.filter(schema__in=schemata),
                       lambda ss: ss.schema
                   )]

        # Deal with schemata with no selectors (since they're not
        # picked up by the groupby expression above).
        empties = schemata.exclude(pk__in=[k.pk for k, g in grouped])
        grouped += [(s, ()) for s in empties]

        # Find matches and return schemas as a queryset.
        pks = map(lambda g: g[0].pk,
                  filter(lambda g: g[1] == selectors, grouped))
        return self.filter(pk__in=pks)

    def from_instance(self, instance):
        content_type = ContentType.objects.get_for_model(instance)
        selectors = ()
        schemas = list(self.by_selectors(content_type, selectors))
        for s in settings.JSONATTRS_SCHEMA_SELECTORS:
            field = s
            if isinstance(s, tuple):
                selector = instance
                for step in s[1]:
                    selector = getattr(selector, step, None)
            else:
                selector = getattr(instance, field, None)
            selectors = selectors + (selector,)
            schemas += list(self.by_selectors(content_type, selectors))
        return schemas


class Schema(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)

    def __str__(self):
        return '<Schema #{}: {}>'.format(
            self.id,
            self.content_type if self.content_type_id is not None else 'None'
        )

    def __repr__(self):
        return str(self)

    @classmethod
    def check_unique_together(cls, content_type, check, exclude=None):
        """Check "unique together" constraint across schema.content_type and
        [sel.selector for sel in schema.selectors.all()].

        """

        # Find possible matching schemata based on content type
        # (excluding the schema being validated).
        schemata = Schema.objects.filter(
            content_type=content_type
        )
        if exclude is not None:
            schemata = schemata.exclude(pk=exclude.pk)

        # Retrieve selector objects from schema selectors for these
        # schemata, grouping by schema (they'll be returned in index
        # order).
        sels = SchemaSelector.objects.filter(schema__in=schemata)
        selectors = []
        for schema in schemata:
            tmp = tuple(map(lambda ss: ss.selector,
                            filter(lambda ss: ss.schema == schema, sels)))
            selectors.append(tmp)

        # If the selector object tuple for the schema being validated
        # occurs in the list of selector object tuples retrieved for
        # existing schemata for the same content type, then the
        # "unique together" constraint for "content type plus
        # selectors" is violated.
        if check in selectors:
            raise ValidationError(
                message="Non-unique schema selectors in jsonattrs",
                code='unique_together'
            )

    def validate_unique(self, *args, **kwargs):
        # Make a tuple of selector objects for the schema being
        # validated.
        check = tuple(s.selector for s in self.selectors.all())
        self.check_unique_together(self.content_type, check, exclude=self)

    objects = SchemaManager()


class SchemaSelector(models.Model):
    schema = models.ForeignKey(Schema, on_delete=models.CASCADE,
                               related_name='selectors')
    index = models.IntegerField()
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=255)
    selector = GenericForeignKey()

    class Meta:
        ordering = ('schema', 'index',)

    def __str__(self):
        return '<SchemaSelector #{} ({}/{}): {}>'.format(
            self.id, self.index, self.schema.selectors.count(),
            self.selector
        )

    def __repr__(self):
        return str(self)


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
        print('validate: value =', value, '(', type(value), ')',
              '  coarse_type =', self.coarse_type,
              '  subtype =', self.subtype)
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
