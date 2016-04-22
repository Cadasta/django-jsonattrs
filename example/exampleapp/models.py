from django.core.urlresolvers import reverse
from django.db import models

from jsonattrs.fields import JSONAttributeField


class Division(models.Model):
    name = models.CharField(max_length=100)
    attrs = JSONAttributeField(null=True)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name


class Department(models.Model):
    name = models.CharField(max_length=100)
    division = models.ForeignKey(Division, related_name='departments')
    attrs = JSONAttributeField(null=True)

    class Meta:
        ordering = ('division', 'name')

    def __str__(self):
        return self.name


class Party(models.Model):
    department = models.ForeignKey(Department, related_name='parties')
    name = models.CharField(max_length=100)
    attrs = JSONAttributeField(null=True)

    class Meta:
        ordering = ('department', 'name')

    def get_absolute_url(self):
        return reverse('party-detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.name


class Contract(models.Model):
    department = models.ForeignKey(Department, related_name='contracts')
    responsible = models.ForeignKey(Party)
    attrs = JSONAttributeField(null=True)

    class Meta:
        ordering = ('department', 'pk')

    def get_absolute_url(self):
        return reverse('parcel-detail', kwargs={'pk': self.pk})

    def __str__(self):
        return str(self.pk)
