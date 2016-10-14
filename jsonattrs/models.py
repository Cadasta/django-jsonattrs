from collections import OrderedDict
import re

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import get_language
from django.core.cache import caches
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.fields import JSONField


def schema_cache_key(content_type, selectors):
    return (
        'jsonattrs:schema:' +
        content_type.app_label + ',' + content_type.model + ':' +
        ','.join(str(s) for s in selectors)
    )


class SchemaManager(models.Manager):
    content_type_to_selectors = dict()

    @classmethod
    def invalidate_cache(cls):
        caches['jsonattrs:schema'].clear()

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
        key = schema_cache_key(content_type, selectors)
        cache = caches['jsonattrs:schema']
        cached = cache.get(key)
        if cached is not None:
            return cached

        # Not in cache: build schema list using increasing selector
        # sequences.
        base_schemas = self.filter(content_type=content_type)
        schemas = []
        for i in range(len(selectors) + 1):
            schemas += list(base_schemas.filter(selectors=selectors[:i]))
            cache.set(key, schemas)
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
    default_language = models.CharField(max_length=3, blank=True)

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

    def __str__(self):
        return self.label


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


class AttributeManager(models.Manager):
    def create(self, *args, **kwargs):
        choices = kwargs.get('choices', None)
        choice_labels = kwargs.get('choice_labels', None)
        if choices is not None and choices != []:
            if choice_labels is not None:
                if len(choices) != len(choice_labels):
                    raise ValueError("lengths of choices and choice_labels "
                                     "don't match for Attribute")
                if not all([isinstance(l, str) or isinstance(l, dict)
                            for l in choice_labels]):
                    raise ValueError("non-string choice label in Attribute")
            else:
                allstr = all([isinstance(c, str) for c in choices])
                alltuple2 = all([isinstance(c, tuple) and len(c) == 2 and
                                 isinstance(c[1], str)
                                 for c in choices])
                if not allstr and not alltuple2:
                    raise ValueError("invalid format for choices in Attribute")
                if alltuple2:
                    kwargs['choices'], kwargs['choice_labels'] = zip(*choices)
        elif choice_labels is not None:
            raise ValueError("choice_labels but no choices in Attribute")
        return super().create(*args, **kwargs)


class Attribute(models.Model):
    schema = models.ForeignKey(
        Schema, related_name='attributes', on_delete=models.CASCADE
    )
    name = models.CharField(max_length=256)
    long_name_xlat = JSONField()
    attr_type = models.ForeignKey(AttributeType, on_delete=models.CASCADE)
    index = models.IntegerField()
    choices = ArrayField(models.CharField(max_length=256), null=True)
    choice_labels_xlat = JSONField(null=True)
    default = models.CharField(max_length=256, blank=True)
    required = models.BooleanField(default=False)
    omit = models.BooleanField(default=False)

    class Meta:
        ordering = ('schema', 'index')
        unique_together = (('schema', 'index'), ('schema', 'name'))

    objects = AttributeManager()

    @property
    def long_name(self):
        if self.long_name_xlat is None or isinstance(self.long_name_xlat, str):
            return self.long_name_xlat
        else:
            return self.long_name_xlat.get(
                get_language(),
                self.long_name_xlat[self.schema.default_language]
            )

    @long_name.setter
    def long_name(self, value):
        self.long_name_xlat = value

    @property
    def choice_labels(self):
        if (self.choice_labels_xlat is None or
            (isinstance(self.choice_labels_xlat, (list, tuple)) and
             (len(self.choice_labels_xlat) == 0 or
              isinstance(self.choice_labels_xlat[0], str)))):
            return self.choice_labels_xlat
        else:
            return [cl.get(get_language(), cl[self.schema.default_language])
                    for cl in self.choice_labels_xlat]

    @choice_labels.setter
    def choice_labels(self, value):
        self.choice_labels_xlat = value

    def validate(self, value):
        if (self.required and self.default == '' and
           (value is None or value == '')):
            raise ValidationError(
                _('Missing required field %(field)s'),
                params={'field': self.name}
            )
        if self.choices is not None and self.choices != []:
            if type(value) == list:
                for v in value:
                    if v not in self.choices:
                        raise ValidationError(
                            _('Invalid choice for %(field)s: "%(value)s"'),
                            params={'field': self.name, 'value': v}
                        )
            elif value not in self.choices:
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

    @property
    def choice_dict(self):
        if self.choices is None or self.choices == []:
            return None
        if self.choice_labels is None or self.choice_labels == []:
            return {c: c for c in self.choices}
        else:
            return {c: l for c, l in zip(self.choices, self.choice_labels)}

    def render(self, val):
        if self.choice_dict is None:
            return val
        else:
            if type(val) == list:
                result = []
                for v in val:
                    result.append(self.choice_dict.get(v, v))
                return ', '.join(result)
            else:
                return self.choice_dict.get(val, val)
