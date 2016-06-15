import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError

from .fixtures import create_fixtures
from .models import Organization, Project, Party, Parcel


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
            name='Bilbo Baggins', attrs={}
        )
        assert 'dob' in tstparty.attrs.attributes
        assert 'gender' in tstparty.attrs.attributes
        assert 'education' in tstparty.attrs.attributes
        assert 'homeowner' in tstparty.attrs.attributes
        assert len(tstparty.attrs.attributes) == 4

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
            name='Bilbo Baggins', attrs={'homeowner': True}
        )
        assert len(tstparty1.attrs.attributes) == 4
        assert tstparty1.attrs['homeowner'] is True
        with pytest.raises(ValidationError):
            Party.objects.create(
                project=self.fixtures['proj11'],
                name='Bilbo Baggins', attrs={'homeowner': 'foo'}
            )

    def test_attributes_lookup_keys(self):
        assert Party.objects.count() == 45
        assert Party.objects.filter(attrs__has_key='homeowner').count() == 10

    def test_attributes_lookup_dict(self):
        assert Party.objects.count() == 45
        print([(p.name, p.attrs) for p in Party.objects.all()])
        assert Party.objects.filter(attrs={'homeowner': 'False'}).count() == 10


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
