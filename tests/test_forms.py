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
        assert isinstance(form.fields['attrs::quality'], forms.ChoiceField)
        assert len(form.fields) == 4

    def test_simple_create_unbound_form(self):
        form = ProjectForm(
            schema_selectors=(self.fixtures['org1'].pk,)
        )
        assert form.attributes_field == 'attrs'
        assert 'name' in form.fields
        assert 'attrs::head' in form.fields
        assert len(form.fields) == 2

    def test_create_unbound_form_field_types_1(self):
        form = PartyForm(
            schema_selectors=(self.fixtures['org1'].pk,
                              self.fixtures['proj11'].pk)
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
            schema_selectors=(self.fixtures['org1'].pk,
                              self.fixtures['proj11'].pk)
        )
        assert form.attributes_field == 'attrs'
        assert 'address' in form.fields
        assert 'project' in form.fields
        assert 'type' in form.fields
        assert 'attrs::quality' in form.fields
        assert isinstance(form.fields['attrs::quality'], forms.ChoiceField)
        assert len(form.fields) == 4

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


# class FormSaveTest(FormTestBase):
#     def setUp(self):
#         super().setUp()
#         self.party = self.fixtures['party111']
#         self.data = {
#             'name': self.party.name,
#             'project': self.party.project.name
#         }

#     def _save(self, data, count=1):
#         form = PartyForm(data, instance=self.party)
#         form.save()
#         assert form.is_valid() is True

#     def test_form_save_valid(self):
#         self._save(self.data)
