from django import forms
from django.forms.widgets import HiddenInput
from django.forms.models import inlineformset_factory
from django.contrib.contenttypes.models import ContentType

from jsonattrs.models import Schema, Attribute

from .models import Division, Department


class AttributeInlineFormSet(forms.BaseInlineFormSet):
    def clean(self):
        print('AttributeInlineFormSet.clean')
        print(self)
        print(self.data)
        super().clean()


AttributeFormSet = inlineformset_factory(
    Schema, Attribute, formset=AttributeInlineFormSet,
    fields=('name', 'long_name', 'coarse_type', 'subtype', 'index',
            'choices', 'default', 'required', 'omit'),
    widgets={'index': HiddenInput(), 'DELETE': HiddenInput()}
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

    def clean(self):
        cleaned_data = super().clean()
        content_type = cleaned_data.get('content_type')
        division = cleaned_data.get('division')
        department = cleaned_data.get('department')
        print('SchemaForm: clean')
        print('  content_type =', content_type)
        print('  division =', division)
        print('  department =', department)
        check = ()
        if division is not None:
            division = Division.objects.get(name=division)
            check = (division,)
            if department is not None:
                department = Department.objects.get(name=department)
                check = (division, department)
        print('Calling Schema.check_unique_together: check =', check)
        Schema.check_unique_together(content_type, check)
