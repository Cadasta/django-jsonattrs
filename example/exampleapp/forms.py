from django import forms
from django.forms.widgets import HiddenInput
from django.contrib.contenttypes.models import ContentType

from jsonattrs.models import Schema, Attribute

from .models import Division, Department


AttributeFormSet = forms.inlineformset_factory(
    Schema, Attribute,
    fields=('name', 'long_name', 'coarse_type', 'subtype', 'index',
            'choices', 'default', 'required', 'omit'),
    widgets={'index': HiddenInput(), 'DELETE': HiddenInput()},
    extra=3
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
        check = ()
        if division is not None:
            division = Division.objects.get(name=division)
            check = (division,)
            if department is not None:
                department = Department.objects.get(name=department)
                check = (division, department)
        Schema.check_unique_together(content_type, check)
