import pytest
from decimal import Decimal
from datetime import date, datetime
from django.test import TestCase
from django.core.exceptions import ValidationError

from .factories import OrganizationFactory
from .fixtures import create_fixtures
from .models import Organization, Project, Party, Parcel
from jsonattrs.fields import convert


def test_convert_decimal():
    val = Decimal('1.1')
    assert convert(val) == 1.1


def test_convert_date():
    val = date(2017, 1, 12)
    assert convert(val) == '2017-01-12'


def test_convert_datetime():
    val = datetime(2017, 1, 12, 13, 6, 11)
    assert convert(val) == '2017-01-12T13:06:11'


def test_convert_unknown():
    val = ValidationError('Some Error')
    with pytest.raises(TypeError) as e:
        convert(val)
    assert 'ValidationError can not be converted to JSON.' == str(e.value)


class FieldTestBase(TestCase):
    def setUp(self):
        self.fixtures, self.schemata = create_fixtures()


class FieldSchemaTest(FieldTestBase):
    def test_schema_from_field(self):
        assert (self.fixtures['org1'].attrs.schemas ==
                [self.schemata['org-default']])

    def test_schema_composition(self):
        tstparty = Party.objects.create(
            project=self.fixtures['proj11'],
            name='Bilbo Baggins', attrs={'dob': '1972-05-10'}
        )
        assert 'dob' in tstparty.attrs.attributes
        assert 'gender' in tstparty.attrs.attributes
        assert 'education' in tstparty.attrs.attributes
        assert 'homeowner' in tstparty.attrs.attributes
        assert len(tstparty.attrs.attributes) == 4

        party = Party.objects.get(name='Bilbo Baggins')
        assert 'dob' in party.attrs
        assert 'homeowner' in party.attrs

    def test_schema_composition_with_omit(self):
        tstparty = Party.objects.create(
            project=self.fixtures['proj12'],
            name='Frodo Baggins', attrs={}
        )
        assert 'dob' not in tstparty.attrs.attributes
        assert 'gender' in tstparty.attrs.attributes
        assert 'education' in tstparty.attrs.attributes
        assert 'homeowner' in tstparty.attrs.attributes
        assert len(tstparty.attrs.attributes) == 3
        with pytest.raises(KeyError):
            print(tstparty.attrs['dob'])
        with pytest.raises(KeyError):
            tstparty.attrs['dob'] = '1984-05-03'
        with pytest.raises(KeyError):
            del tstparty.attrs['dob']


class FieldAttributeTest(FieldTestBase):
    def test_validate_unknown_key(self):
        with pytest.raises(ValidationError) as e:
            Organization.objects.create(
                name='tstorg',
                attrs={'home_office': 'London', 'unknown': False}
            )
        assert 'Unknown key "unknown"' in e.value

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
            attrs={'gender': 'male', 'homeowner': True,
                   'education': 'masters', 'dob': '1954-02-12'}
        )
        assert tstparty.attrs['homeowner'] is True
        tstparty.attrs['homeowner'] = False
        assert tstparty.attrs['homeowner'] is False
        with pytest.raises(KeyError):
            tstparty.attrs['foo'] = 'bar'
        assert len(tstparty.attrs) == 4
        del tstparty.attrs['gender']
        assert len(tstparty.attrs) == 3
        with pytest.raises(KeyError):
            del tstparty.attrs['homeowner']
        assert len(tstparty.attrs) == 3

    def test_attributes_choice_validation(self):
        tstparcel1 = Parcel.objects.create(
            project=self.fixtures['proj11'],
            address='Bag End, Hobbiton', attrs={'quality': 'point'}
        )
        assert len(tstparcel1.attrs.attributes) == 2
        assert tstparcel1.attrs['quality'] == 'point'
        with pytest.raises(ValidationError):
            Parcel.objects.create(
                project=self.fixtures['proj11'],
                address='Bag End, Hobbiton', attrs={'quality': 'foo'}
            )

        tstparcel2 = Parcel.objects.create(
            project=self.fixtures['proj11'],
            address='The Shire',
            attrs={
                'quality': 'point',
                'infrastructure': ['water', 'food']
                }
        )
        assert len(tstparcel1.attrs.attributes) == 2
        assert tstparcel2.attrs['infrastructure'] == ['water', 'food']
        with pytest.raises(ValidationError):
            Parcel.objects.create(
                project=self.fixtures['proj11'],
                address='The Shire', attrs={'infrastructure': ['foo', 'bar']}
            )

    def test_attributes_required_validation(self):
        with pytest.raises(ValidationError):
            Party.objects.create(
                project=self.fixtures['proj11'],
                name='Bilbo Baggins',
                attrs={'homeowner': True}
            )
        with pytest.raises(ValidationError):
            party = Party.objects.create(
                project=self.fixtures['proj11'],
                name='Bilbo Baggins',
                attrs={'homeowner': True, 'dob': '1975-11-06'}
            )
            party.attrs['dob'] = None

    def test_attributes_other_validation(self):
        tstparty1 = Party.objects.create(
            project=self.fixtures['proj11'],
            name='Bilbo Baggins',
            attrs={'homeowner': True, 'dob': '1972-05-10'}
        )
        assert len(tstparty1.attrs.attributes) == 4
        assert tstparty1.attrs['homeowner'] is True
        with pytest.raises(ValidationError):
            Party.objects.create(
                project=self.fixtures['proj11'],
                name='Bilbo Baggins',
                attrs={'homeowner': 'foo', 'dob': '1989-10-12'}
            )
        with pytest.raises(ValidationError):
            Party.objects.create(
                project=self.fixtures['proj11'],
                name='Bilbo Baggins',
                attrs={'homeowner': 3, 'dob': '1989-10-12'}
            )

    def test_attributes_lookup_keys(self):
        assert Party.objects.count() == 45
        assert Party.objects.filter(attrs__has_key='homeowner').count() == 10

    def test_attributes_lookup_dict(self):
        assert Party.objects.count() == 45
        assert Party.objects.filter(attrs={'homeowner': 'False'}).count() == 5

    def test_cast_to_dict_with_unknown_attr(self):
        """
        Ensure that data with unknown attributes can still be cast to dict.
        This is used by DRF's JSONRenderer to render models with a
        JSONAttribute field to JSON.
        """
        prj = Organization.objects.bulk_create([  # Skip validation on create
            OrganizationFactory.build(attrs={'foo': 'bar'})
        ])[0]
        assert dict(prj.attrs) == {'foo': 'bar'}


class FieldDbTest(FieldTestBase):
    def test_check_fixtures(self):
        assert Organization.objects.count() == 3
        assert Project.objects.count() == 9
        assert all(org.project_set.count() == 3
                   for org in Organization.objects.all())
        assert Parcel.objects.count() == 45
        assert all(prj.parcel_set.count() == 5
                   for prj in Project.objects.all())
        assert Party.objects.count() == 45
        assert all(prj.party_set.count() == 5
                   for prj in Project.objects.all())

    def test_set_attribute_and_save(self):
        prj = Project.objects.get(name='Project #1.1')
        prj.attrs['head'] = 'Jim Jimson'
        prj.save()
        prj_check = Project.objects.get(name='Project #1.1')
        assert prj_check.attrs['head'] == 'Jim Jimson'
