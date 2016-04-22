import itertools
import factory

from jsonattrs.models import Schema, SchemaSelector
from .models import Organization, Project, Party, Parcel


class SchemaFactory:
    @staticmethod
    def create(content_type, selectors):
        schema = Schema.objects.create(content_type=content_type)
        for selector, index in zip(selectors, itertools.count(1)):
            SchemaSelector.objects.create(
                schema=schema, index=index, selector=selector
            )
        return schema


class OrganizationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Organization

    name = factory.Sequence(lambda n: "Organization #%s" % n)


class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Project

    name = factory.Sequence(lambda n: "Project #%s" % n)


class PartyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Party

    name = factory.Sequence(lambda n: "Party #%s" % n)


class ParcelFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Parcel

    address = factory.Sequence(lambda n: "Parcel #%s" % n)
