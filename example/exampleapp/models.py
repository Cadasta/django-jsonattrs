from django.core.urlresolvers import reverse
from django.db import models

from jsonattrs.fields import JSONAttributeField
from jsonattrs.decorators import fix_model_for_attributes


@fix_model_for_attributes
class Division(models.Model):
    name = models.CharField(max_length=100)
    attrs = JSONAttributeField()

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name


@fix_model_for_attributes
class Department(models.Model):
    name = models.CharField(max_length=100)
    division = models.ForeignKey(Division, related_name='departments')
    attrs = JSONAttributeField()

    class Meta:
        ordering = ('division', 'name')

    def __str__(self):
        return self.name


@fix_model_for_attributes
class Party(models.Model):
    department = models.ForeignKey(Department, related_name='parties')
    name = models.CharField(max_length=100)
    attrs = JSONAttributeField()

    class Meta:
        ordering = ('department', 'name')

    def get_absolute_url(self):
        return reverse('party-detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.name


@fix_model_for_attributes
class Contract(models.Model):
    department = models.ForeignKey(Department, related_name='contracts')
    responsible = models.ForeignKey(Party)
    attrs = JSONAttributeField()

    class Meta:
        ordering = ('department', 'pk')

    def get_absolute_url(self):
        return reverse('parcel-detail', kwargs={'pk': self.pk})

    def __str__(self):
        return str(self.pk)
