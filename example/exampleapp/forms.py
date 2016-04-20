from django import forms
from django.contrib.contenttypes.models import ContentType

from .models import Organization, Project


class SchemaForm(forms.Form):
    content_type = forms.ModelChoiceField(
        queryset=ContentType.objects.filter(app_label='exampleapp'),
        empty_label=None, required=True
    )
    organization = forms.ModelChoiceField(
        queryset=Organization.objects.all(), empty_label='*', required=False
    )
    project = forms.ModelChoiceField(
        queryset=Project.objects.all(), empty_label='*', required=False
    )
