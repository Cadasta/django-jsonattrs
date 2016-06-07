from django import forms
from django.forms.widgets import HiddenInput
from django.forms.models import inlineformset_factory
from django.contrib.contenttypes.models import ContentType

from jsonattrs.models import Schema, Attribute
from jsonattrs.forms import AttributeModelForm

from .models import Division, Department, Party, Contract


class AttributeInlineFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        names = []
        for form in self.forms:
            name = form.cleaned_data['name']
            if name in names:
                raise forms.ValidationError("Field names must be unique.")
            names.append(name)


AttributeFormSet = inlineformset_factory(
    Schema, Attribute, formset=AttributeInlineFormSet,
    fields=('name', 'long_name', 'coarse_type', 'subtype', 'index',
            'choices', 'default', 'required', 'omit'),
    widgets={'index': HiddenInput(), 'DELETE': HiddenInput()},
    extra=0
)


class SchemaForm(forms.Form):
    content_type = forms.ModelChoiceField(
        queryset=ContentType.objects.filter(app_label='exampleapp'),
        empty_label=None, required=True
    )
    division = forms.ModelChoiceField(
        queryset=Division.objects.all(), empty_label='*', required=False
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(), empty_label='*', required=False
    )

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('instance', None)
        super().__init__(*args, **kwargs)


class DivisionForm(AttributeModelForm):
    attributes_field = 'attrs'

    class Meta:
        model = Division
        fields = ('name',)


class DepartmentForm(AttributeModelForm):
    attributes_field = 'attrs'

    class Meta:
        model = Department
        fields = ('name', 'division')


class PartyForm(AttributeModelForm):
    attributes_field = 'attrs'

    class Meta:
        model = Party
        fields = ('department', 'name')


class ContractForm(AttributeModelForm):
    attributes_field = 'attrs'

    class Meta:
        model = Contract
        fields = ('department', 'responsible')
