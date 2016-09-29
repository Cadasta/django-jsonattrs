import pytest

from django import forms
from django.test import TestCase

from jsonattrs.forms import AttributeModelForm
from jsonattrs.models import (
    Schema, Attribute, create_attribute_type, AttributeType
)

from .fixtures import create_fixtures
from .models import Project, Party, Parcel


class ProjectForm(AttributeModelForm):
    attributes_field = 'attrs'

    class Meta:
        model = Project
        fields = ('name',)


class PartyForm(AttributeModelForm):
    attributes_field = 'attrs'

    class Meta:
        model = Party
        fields = ('name', 'project')


class ParcelForm(AttributeModelForm):
    attributes_field = 'attrs'

    class Meta:
        model = Parcel
        fields = ('address', 'type', 'project')


class FormTestBase(TestCase):
    def setUp(self):
        self.fixtures, self.schemata = create_fixtures()


class FormCreationTest(FormTestBase):
    def test_simple_create_bound_form(self):
        proj = self.fixtures['proj11']
        form = ProjectForm(instance=proj)
        assert form.attributes_field == 'attrs'
        assert 'name' in form.fields
        assert 'attrs::head' in form.fields
        assert len(form.fields) == 2

    def test_create_bound_form_field_types_1(self):
        party = self.fixtures['party111']
        form = PartyForm(instance=party)
        assert form.attributes_field == 'attrs'
        assert 'name' in form.fields
        assert 'project' in form.fields
        assert 'attrs::dob' in form.fields
        assert isinstance(form.fields['attrs::dob'], forms.DateField)
        assert 'attrs::gender' in form.fields
        assert isinstance(form.fields['attrs::gender'], forms.CharField)
        assert 'attrs::education' in form.fields
        assert isinstance(form.fields['attrs::education'], forms.CharField)
        assert 'attrs::homeowner' in form.fields
        assert isinstance(form.fields['attrs::homeowner'], forms.BooleanField)
        assert len(form.fields) == 6

    def test_create_bound_form_field_types_2(self):
        parcel = self.fixtures['parcel111']
        form = ParcelForm(instance=parcel)
        assert form.attributes_field == 'attrs'
        assert 'address' in form.fields
        assert 'project' in form.fields
        assert 'type' in form.fields
        assert 'attrs::quality' in form.fields
        assert 'attrs::infrastructure' in form.fields
        assert isinstance(form.fields['attrs::quality'], forms.ChoiceField)
        assert len(form.fields) == 5
        labels = [ch[1] for ch in form.fields['attrs::quality'].choices]
        assert 'None' in labels
        assert 'Textual' in labels
        print(labels)

    def test_simple_create_unbound_form(self):
        form = ProjectForm(
            schema_selectors=(
                {'name': 'organisation',
                 'value': self.fixtures['org1'],
                 'selector': self.fixtures['org1'].pk},
            )
        )
        assert form.attributes_field == 'attrs'
        assert 'name' in form.fields
        assert 'attrs::head' in form.fields
        assert len(form.fields) == 2

    def test_create_unbound_form_field_types_1(self):
        form = PartyForm(
            schema_selectors=(
                {'name': None,
                 'selector': self.fixtures['org1'].pk},
                {'name': 'project',
                 'value': self.fixtures['proj11'],
                 'selector': self.fixtures['proj11'].pk}
            )
        )
        assert form.attributes_field == 'attrs'
        assert 'name' in form.fields
        assert 'project' in form.fields
        assert 'attrs::dob' in form.fields
        assert isinstance(form.fields['attrs::dob'], forms.DateField)
        assert 'attrs::gender' in form.fields
        assert isinstance(form.fields['attrs::gender'], forms.CharField)
        assert 'attrs::education' in form.fields
        assert isinstance(form.fields['attrs::education'], forms.CharField)
        assert 'attrs::homeowner' in form.fields
        assert isinstance(form.fields['attrs::homeowner'], forms.BooleanField)
        assert len(form.fields) == 6

    def test_create_unbound_form_field_types_2(self):
        form = ParcelForm(
            schema_selectors=(
                {'name': None,
                 'selector': self.fixtures['org1'].pk},
                {'name': 'project',
                 'value': self.fixtures['proj11'],
                 'selector': self.fixtures['proj11'].pk}
            )
        )
        assert form.attributes_field == 'attrs'
        assert 'address' in form.fields
        assert 'project' in form.fields
        assert 'type' in form.fields
        assert 'attrs::quality' in form.fields
        assert 'attrs::infrastructure' in form.fields
        assert isinstance(form.fields['attrs::quality'], forms.ChoiceField)
        assert len(form.fields) == 5

    def test_create_bad_fieldname(self):
        create_attribute_type('bad', 'Bad', 'BadField')
        party = self.fixtures['party111']
        schema = Schema.objects.from_instance(party)[-1]
        badattrtype = AttributeType.objects.get(name='bad')
        Attribute.objects.create(
            schema=schema, name='badattr', long_name='Bad attribute',
            attr_type=badattrtype, index=10
        )
        with pytest.raises(ValueError):
            PartyForm(instance=party)


class FormSaveTest(FormTestBase):
    def setUp(self):
        super().setUp()
        self.party = self.fixtures['party111']
        self.proj = self.fixtures['proj11']
        self.data = {
            'name': self.party.name,
            'project': self.proj.pk,
            'attrs::dob': '1975-11-06',
            'attrs::gender': 'female',
            'attrs::education': 'high-school'
        }
        self.unbound_data = {
            'name': 'New party',
            'project': self.proj.pk,
            'attrs::dob': '1976-10-15',
            'attrs::gender': 'male',
            'attrs::education': 'none'
        }

    def _count(self, count):
        assert Party.objects.count() == count

    def test_form_save_bound_valid(self):
        self._count(45)
        form = PartyForm(self.data, instance=self.party)
        assert form.is_valid() is True
        form.save()
        self._count(45)

    def test_form_save_bound_missing_required_attribute(self):
        self._count(45)
        del self.data['attrs::dob']
        form = PartyForm(self.data, instance=self.party)
        assert form.is_valid() is False
        assert len(form.errors) == 1
        assert form.errors['attrs::dob'] == ['This field is required.']
        self._count(45)

    def test_form_save_unbound_valid(self):
        self._count(45)
        form = PartyForm(
            self.unbound_data,
            schema_selectors=(
                {'name': None, 'selector': self.proj.organization.pk},
                {'name': 'project', 'selector': self.proj.pk,
                 'value': self.proj}
            )
        )
        assert form.is_valid() is True
        form.save()
        self._count(46)
