from collections import OrderedDict
import re

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField


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
            selectors = self._get_selectors(instance, content_type)
        selectors = tuple(selectors)
        if any(s is None for s in selectors):
            return None

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

    def _get_selectors(self, instance, content_type=None):
        if content_type is None:
            content_type = ContentType.objects.get_for_model(instance)

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
        return tuple(selectors)


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
    default_attrs = {n for n, a in attrs.items()
                     if a.default is not None and a.default != ''}

    return attrs, required_attrs, default_attrs


def create_attribute_type(name, label, form_field,
                          widget=None, validator_re=None, validator_type=None):
    if not AttributeType.objects.filter(name=name).exists():
        AttributeType.objects.create(
            name=name, label=label, form_field=form_field, widget=widget,
            validator_re=validator_re, validator_type=validator_type
        )


class AttributeType(models.Model):
    name = models.CharField(max_length=256)
    label = models.CharField(max_length=512)
    form_field = models.CharField(max_length=256)
    widget = models.CharField(max_length=256, null=True, blank=True)
    validator_re = models.CharField(max_length=512, null=True, blank=True)
    validator_type = models.CharField(max_length=256, null=True, blank=True)


def create_attribute_types():
    create_attribute_type('boolean', 'Boolean', 'BooleanField',
                          validator_type='bool',
                          validator_re=r'true|false|True|False')

    create_attribute_type('text', 'Text', 'CharField',
                          validator_type='str')
    create_attribute_type('text_multiline', 'Multiline text', 'CharField',
                          validator_type='str',
                          widget='Textarea')

    create_attribute_type('date', 'Date', 'DateField')
    create_attribute_type('dateTime', 'Date and time', 'DateTimeField')
    create_attribute_type('time', 'Time', 'TimeField')

    create_attribute_type('integer', 'Integer', 'IntegerField',
                          validator_re=r'[-+]?\d+')
    create_attribute_type('decimal', 'Decimal number', 'DecimalField',
                          validator_re=r'[-+]?\d+(\.\d+)?')

    create_attribute_type('email', 'Email address', 'EmailField')
    create_attribute_type('url', 'URL', 'URLField')

    create_attribute_type('select_one', 'Select one:', 'ChoiceField')
    create_attribute_type('select_multiple', 'Select multiple:',
                          'MultipleChoiceField')
    create_attribute_type('foreign_key', 'Select one:', 'ModelChoiceField')


# Sigh.  Oh Python.  Really?  Why?  Is there really no other way to
# look up a class by name than to manually calculate the transitive
# closure of the subclass relationship starting from "object"?

def desc_classes(c):
    try:
        scs = c.__subclasses__()
        sscs = []
        for sc in scs:
            sscs += desc_classes(sc)
        scs += sscs
        return scs
    except:
        return []


class_cache = None


def find_class(name):
    global class_cache

    if class_cache is None:
        class_cache = desc_classes(object)
    return [c for c in class_cache if c.__name__ == name][0]


class Attribute(models.Model):
    schema = models.ForeignKey(
        Schema, related_name='attributes', on_delete=models.CASCADE
    )
    name = models.CharField(max_length=256)
    long_name = models.CharField(max_length=512, blank=True)
    attr_type = models.ForeignKey(AttributeType, on_delete=models.CASCADE)
    index = models.IntegerField()
    choices = ArrayField(models.CharField(max_length=256), null=True)
    default = models.CharField(max_length=256, blank=True)
    required = models.BooleanField(default=False)
    omit = models.BooleanField(default=False)

    class Meta:
        ordering = ('schema', 'index')
        unique_together = (('schema', 'index'), ('schema', 'name'))

    def validate(self, value):
        if (self.required and self.default == '' and
           (value is None or value == '')):
            raise ValidationError(
                _('Missing required field %(field)s'),
                params={'field': self.name}
            )
        if self.choices is not None and self.choices != []:
            if value not in self.choices:
                raise ValidationError(
                    _('Invalid choice for %(field)s: "%(value)s"'),
                    params={'field': self.name, 'value': value}
                )
        atype = self.attr_type
        if isinstance(value, str):
            if (atype.validator_re is not None and
               re.match(atype.validator_re, value) is None):
                raise ValidationError(
                    _('Validation failed for %(field)s: "%(value)s"'),
                    params={'field': self.name, 'value': value}
                )
        elif atype.validator_type is not None:
            if not isinstance(value, find_class(atype.validator_type)):
                raise ValidationError(
                    _('Validation failed for %(field)s: "%(value)s"'),
                    params={'field': self.name, 'value': value}
                )
