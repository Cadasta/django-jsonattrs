# import pytest
from django.test import TestCase

from jsonattrs.fields import JSONAttributes

from .fixtures import create_object_fixtures, create_schema_fixtures
from .models import Organization


class FieldTest(TestCase):
    def setUp(self):
        self.fixtures = create_object_fixtures()
        self.schemata = create_schema_fixtures(self.fixtures)

    def test_schema_from_field(self):
        tstorg = Organization.objects.create(name='testorg')
        print(tstorg._meta.get_field('attrs'))
        print(tstorg._meta.get_field('attrs').__class__)
        print(dir(tstorg._meta.get_field('attrs')))
        assert (self.fixtures['org1'].attrs.schema() ==
                self.schemata['org-default'])

    def test_attributes_assignment(self):
        tstorg = Organization.objects.create(name='testorg')
        assert len(tstorg.attrs.attributes) == 1
        assert tstorg.attrs['home_office'] == 'New York'

    def test_attributes_dictionary(self):
        attrs = JSONAttributes(self.schemata['org-default'],
                               home_office='Igls')
        print(attrs)
        print(dir(Organization._meta.fields[2]))
        assert False

    def test_attributes_from_field(self):
        pass
