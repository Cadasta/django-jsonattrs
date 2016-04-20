import factory

from .models import Organization, Project, Party, Parcel


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
