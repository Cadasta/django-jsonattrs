from itertools import groupby

from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from .settings import FIELD_TYPES


class Schema(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)

    def __str__(self):
        return '<Schema #{}: {}>'.format(self.id, self.content_type)

    def __repr__(self):
        return str(self)

    def validate_unique(self, *args, **kwargs):
        """Need to maintain the unique together constraint across
        schema.content_type and [sel.selector for sel in
        schema.selectors.all()].

        """

        # Find possible matching schemata based on content type
        # (excluding the schema being validated).
        schemata = Schema.objects.filter(
            content_type=self.content_type
        ).exclude(pk=self.pk)

        # Retrieve schema selectors for these schemata, grouping by
        # schema (they'll be returned in index order).
        selectors_tmp = [
            tuple(g[1]) for g
            in groupby(SchemaSelector.objects.filter(schema__in=schemata),
                       lambda ss: ss.schema)
        ]

        # Make a list of tuples of selector objects for each schema
        # for us to match against the selector objects of the schema
        # being validated.
        selectors = list(map(lambda ss: tuple([s.selector for s in ss]),
                             selectors_tmp))

        # Make a tuple of selector objects for the schema being
        # validated.
        check = tuple([s.selector for s in self.selectors.all()])

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


class Attribute(models.Model):
    name = models.CharField(max_length=50)
    long_name = models.CharField(max_length=50, blank=True)
    schema = models.ForeignKey(Schema, related_name='fields')
    type = models.CharField(max_length=255, choices=FIELD_TYPE_CHOICES)
    subtype = models.CharField(max_length=255, blank=True)
    related_model = models.ForeignKey(ContentType, null=True)
    order = models.IntegerField()
    unique_together = models.BooleanField()
    unique = models.BooleanField()
    choices = models.CharField(max_length=200, blank=True)
    default = models.CharField(max_length=50, blank=True)
    required = models.BooleanField(default=False)
    omit = models.BooleanField(default=False)
