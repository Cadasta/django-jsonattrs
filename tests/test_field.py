import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError

from .fixtures import create_object_fixtures, create_schema_fixtures
from .models import Organization, Party, Parcel


class FieldTestBase(TestCase):
    def setUp(self):
        self.fixtures = create_object_fixtures()
        self.schemata = create_schema_fixtures(self.fixtures)


class FieldSchemaTest(FieldTestBase):
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

    def test_schema_composition_with_omit(self):
        tstparty = Party.objects.create(
            project=self.fixtures['proj12'],
            name='Frodo Baggins', attrs={}
        )
        assert 'dob' not in tstparty.attrs.attributes
        assert 'gender' in tstparty.attrs.attributes
        assert 'education' in tstparty.attrs.attributes
        assert 'owner' in tstparty.attrs.attributes
        assert len(tstparty.attrs.attributes) == 3
        with pytest.raises(KeyError):
            print(tstparty.attrs['dob'])
        with pytest.raises(KeyError):
            tstparty.attrs['dob'] = '1984-05-03'
        with pytest.raises(KeyError):
            del tstparty.attrs['dob']


class FieldAttributeTest(FieldTestBase):
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

    def test_attributes_key_validation(self):
        tstparty = Party.objects.create(
            project=self.fixtures['proj11'],
            name='Bilbo Baggins',
            attrs={'gender': 'male', 'owner': True,
                   'education': 'masters', 'dob': '1954-02-12'}
        )
        assert tstparty.attrs['owner'] is True
        tstparty.attrs['owner'] = False
        assert tstparty.attrs['owner'] is False
        with pytest.raises(KeyError):
            tstparty.attrs['foo'] = 'bar'
        assert len(tstparty.attrs) == 4
        del tstparty.attrs['gender']
        assert len(tstparty.attrs) == 3
        with pytest.raises(KeyError):
            del tstparty.attrs['owner']
        assert len(tstparty.attrs) == 3

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
