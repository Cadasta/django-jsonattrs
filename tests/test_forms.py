from django import forms
from django.test import TestCase

from jsonattrs.forms import AttributeModelForm

from .fixtures import create_fixtures
from .models import Project, Party


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

    def test_create_bound_form_field_types(self):
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
