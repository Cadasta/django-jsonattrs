import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError

from .fixtures import create_object_fixtures, create_schema_fixtures
from .models import Organization, Party, Parcel


class FieldTest(TestCase):
    def setUp(self):
        self.fixtures = create_object_fixtures()
        self.schemata = create_schema_fixtures(self.fixtures)

    def test_schema_from_field(self):
        assert (self.fixtures['org1'].attrs.schemas ==
                [self.schemata['org-default']])

    def test_schema_composition(self):
        tstparty = Party.objects.create(
            project=self.fixtures['proj11'],
            name='Bilbo Baggins', attrs={}
        )
        assert 'dob' in tstparty.attrs.attributes
        assert 'gender' in tstparty.attrs.attributes
        assert 'education' in tstparty.attrs.attributes
        assert 'owner' in tstparty.attrs.attributes
        assert len(tstparty.attrs.attributes) == 4

    def test_attributes_defaults(self):
        tstorg = Organization.objects.create(name='tstorg')
        assert len(tstorg.attrs.attributes) == 1
        assert tstorg.attrs['home_office'] == 'New York'

    def test_attributes_init(self):
        tstorg = Organization.objects.create(
            name='tstorg', attrs={'home_office': 'London'}
        )
        assert len(tstorg.attrs.attributes) == 1
        assert tstorg.attrs['home_office'] == 'London'

    def test_attributes_choice_validation(self):
        tstparcel1 = Parcel.objects.create(
            project=self.fixtures['proj11'],
            address='Bag End, Hobbiton', attrs={'quality': 'point'}
        )
        assert len(tstparcel1.attrs.attributes) == 1
        assert tstparcel1.attrs['quality'] == 'point'
        with pytest.raises(ValidationError):
            Parcel.objects.create(
                project=self.fixtures['proj11'],
                address='Bag End, Hobbiton', attrs={'quality': 'foo'}
            )

    def test_attributes_other_validation(self):
        tstparty1 = Party.objects.create(
            project=self.fixtures['proj11'],
            name='Bilbo Baggins', attrs={'owner': True}
        )
        assert len(tstparty1.attrs.attributes) == 4
        assert tstparty1.attrs['owner'] is True
        with pytest.raises(ValidationError):
            Party.objects.create(
                project=self.fixtures['proj11'],
                name='Bilbo Baggins', attrs={'owner': 'foo'}
            )

    def test_attributes_dictionary(self):
        # attrs = JSONAttributes(self.schemata['org-default'],
        #                        home_office='Igls')
        pass

    def test_attributes_from_field(self):
        pass
