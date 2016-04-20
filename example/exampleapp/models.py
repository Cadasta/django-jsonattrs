from django.core.urlresolvers import reverse
from django.db import models

from .fields import EntityAttributeField


class Organization(models.Model):
    name = models.CharField(max_length=100)
    attrs = EntityAttributeField(null=True)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name


class Project(models.Model):
    name = models.CharField(max_length=100)
    organization = models.ForeignKey(Organization)
    attrs = EntityAttributeField(null=True)

    class Meta:
        ordering = ('organization', 'name')

    def __str__(self):
        return self.name


class Party(models.Model):
    project = models.ForeignKey(Project)
    name = models.CharField(max_length=100)
    attrs = EntityAttributeField(null=True)

    class Meta:
        ordering = ('project', 'name')

    def get_absolute_url(self):
        return reverse('party-detail', kwargs={'pk': self.pk})


class Parcel(models.Model):
    project = models.ForeignKey(Project)
    address = models.CharField(max_length=200)
    attrs = EntityAttributeField(null=True)

    class Meta:
        ordering = ('project', 'address')

    def get_absolute_url(self):
        return reverse('parcel-detail', kwargs={'pk': self.pk})
