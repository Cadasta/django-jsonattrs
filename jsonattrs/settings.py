from django.conf import settings


DEFAULT_FIELD_TYPES = [
    'BooleanField',
    'CharField',
    'CommaSeparatedIntegerField',
    'DateField',
    'DateTimeField',
    'DecimalField',
    'EmailField',
    'FloatField',
    'NullBooleanField',
    'SlugField',
    'TimeField',
    'URLField',
    'XMLField',
    'BigIntegerField',
    'IntegerField',
    'PositiveIntegerField',
    'PositiveSmallIntegerField',
    'SmallIntegerField'
]
FIELD_TYPES = getattr(settings, 'FIELD_TYPES', DEFAULT_FIELD_TYPES)
