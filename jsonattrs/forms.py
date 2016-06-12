from django import forms
from django.contrib.contenttypes.models import ContentType

from .models import Schema, compose_schemas


FORM_FIELDS = {
    'BooleanField': forms.BooleanField,
    'CharField': forms.CharField,
    'IntegerField': forms.IntegerField,
    'DecimalField': forms.DecimalField,
    'DateField': forms.DateField,
    'DateTimeField': forms.DateTimeField,
    'TimeField': forms.TimeField,
    'EmailField': forms.EmailField,
    'URLField': forms.URLField,
    'ChoiceField': forms.ChoiceField,
    'MultipleChoiceField': forms.MultipleChoiceField
}


def form_field_from_name(name):
    if name in FORM_FIELDS:
        return FORM_FIELDS[name]
    else:
        raise ValueError("Invalid form field name "
                         "for attribute: '{}'".format(name))


class AttributeModelForm(forms.ModelForm):
    attributes_field = None

    def __init__(self, schema_selectors=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.attributes_field is not None:
            self.add_attribute_fields(schema_selectors)

    def add_attribute_fields(self, schema_selectors):
        attrs = None
        attrvals = {}
        schemas = None
        if hasattr(self, 'instance') and self.instance is not None:
            schemas = Schema.objects.from_instance(self.instance)
            attrvals = getattr(self.instance, self.attributes_field)
        elif schema_selectors is not None:
            content_type = ContentType.objects.get_for_model(self.model)
            schemas = Schema.objects.lookup(
                content_type, schema_selectors
            )
        attrs, _, _ = compose_schemas(*schemas)
        for name, attr in attrs.items():
            fieldname = self.attributes_field + '::' + name
            atype = attr.attr_type
            args = {'label': attr.long_name}
            field = form_field_from_name(atype.form_field)
            if atype.name == 'text':
                args['max_length'] = 32
            if attr.name == 'select_one' or attr.name == 'select_multiple':
                args['choices'] = list(map(lambda c: (c, c), attr.choices))
            if attr.name == 'boolean':
                args['required'] = False
                if len(attr.default) > 0:
                    args['initial'] = attr.default != 'False'
            elif attr.required:
                args['required'] = True
                if len(attr.default) > 0:
                    args['initial'] = attr.default
            self.set_initial(args, name, attr, attrvals)
            self.fields[fieldname] = field(**args)

    def set_initial(self, args, name, attr, attrvals):
        if name in attrvals:
            if attr.attr_type.name == 'boolean':
                args['initial'] = attrvals[name] != 'False'
            else:
                args['initial'] = attrvals[name]

    def process_attributes_fields(self):
        chk = self.attributes_field + '::'
        chklen = len(chk)
        attrvals = getattr(self.instance, self.attributes_field)
        for k, v in self.cleaned_data.items():
            if k.startswith(chk):
                k = k[chklen:]
                attrvals[k] = v
                print('Adding:', k, '=', v)
        setattr(self.instance, self.attributes_field, attrvals)

    def save(self, *args, **kwargs):
        print('AttributeModelForm.save')
        if self.attributes_field is not None:
            self.process_attributes_fields()
        return super().save(*args, **kwargs)
