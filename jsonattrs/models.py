from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from .settings import FIELD_TYPES


class Schema(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)

    def __str__(self):
        return '<Schema #{}: {}>'.format(self.id, self.content_type)

    def __repr__(self):
        return str(self)


class SchemaSelector(models.Model):
    schema = models.ForeignKey(Schema, on_delete=models.CASCADE,
                               related_name='selectors')
    index = models.IntegerField()
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=255)
    selector = GenericForeignKey()

    class Meta:
        ordering = ('index',)

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
