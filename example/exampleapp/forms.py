from django import forms
from django.contrib.contenttypes.models import ContentType

from jsonattrs.models import FIELD_TYPE_CHOICES

from .models import Division, Department


class AttributeForm(forms.Form):
    name = forms.CharField(max_length=50)
    long_name = forms.CharField(max_length=50, required=False)
    coarse_type = forms.ChoiceField(choices=FIELD_TYPE_CHOICES)
    subtype = forms.CharField(max_length=255, required=False)
    order = forms.IntegerField()
    unique_together = forms.BooleanField()
    unique = forms.BooleanField()
    choices = forms.CharField(max_length=200, required=False)
    default = forms.CharField(max_length=50, required=False)
    required = forms.BooleanField()
    omit = forms.BooleanField()


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
