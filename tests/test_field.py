# import pytest
from django.test import TestCase

from .fixtures import create_object_fixtures, create_schema_fixtures
from .models import Organization


class FieldTest(TestCase):
    def setUp(self):
        self.fixtures = create_object_fixtures()
        self.schemata = create_schema_fixtures(self.fixtures)

    def test_schema_from_field(self):
        assert (self.fixtures['org1'].attrs.schemas ==
                [self.schemata['org-default']])

    def test_attributes_assignment(self):
        tstorg = Organization.objects.create(name='testorg')
        assert len(tstorg.attrs.attributes) == 1
        assert tstorg.attrs['home_office'] == 'New York'

    def test_attributes_dictionary(self):
        # attrs = JSONAttributes(self.schemata['org-default'],
        #                        home_office='Igls')
        pass

    def test_attributes_from_field(self):
        pass
