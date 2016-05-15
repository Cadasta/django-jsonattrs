from django.core.urlresolvers import reverse
from django.db import models

from jsonattrs.fields import JSONAttributeField
from jsonattrs.decorators import fix_model_for_attributes


@fix_model_for_attributes
class Organization(models.Model):
    name = models.CharField(max_length=100)
    attrs = JSONAttributeField()

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name


@fix_model_for_attributes
class Project(models.Model):
    name = models.CharField(max_length=100)
    organization = models.ForeignKey(Organization)
    attrs = JSONAttributeField()

    class Meta:
        ordering = ('organization', 'name')

    def __str__(self):
        return self.name


@fix_model_for_attributes
class Party(models.Model):
    project = models.ForeignKey(Project)
    name = models.CharField(max_length=100)
    attrs = JSONAttributeField()

    class Meta:
        ordering = ('project', 'name')

    def get_absolute_url(self):
        return reverse('party-detail', kwargs={'pk': self.pk})


@fix_model_for_attributes
class Parcel(models.Model):
    project = models.ForeignKey(Project)
    address = models.CharField(max_length=200)
    attrs = JSONAttributeField()

    class Meta:
        ordering = ('project', 'address')

    def get_absolute_url(self):
        return reverse('parcel-detail', kwargs={'pk': self.pk})
