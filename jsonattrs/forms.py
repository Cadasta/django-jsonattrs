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

    def __init__(self, *args, **kwargs):
        schema_selectors = kwargs.pop('schema_selectors', None)
        super().__init__(*args, **kwargs)
        if self.attributes_field is not None:
            self.add_attribute_fields(schema_selectors)

    def add_attribute_fields(self, schema_selectors):
        attrs = None
        attrvals = getattr(self.instance, self.attributes_field)
        schemas = None
        if self.instance.pk:
            schemas = Schema.objects.from_instance(self.instance)
        elif schema_selectors is not None:
            selectors = []
            for ss in schema_selectors:
                selectors.append(ss['selector'])
                if ss['name'] is not None:
                    setattr(self.instance, ss['name'], ss['value'])
            content_type = ContentType.objects.get_for_model(self.Meta.model)
            schemas = Schema.objects.lookup(
                content_type=content_type, selectors=selectors
            )
            attrvals.setup_schema(schemas)
        attrs, _, _ = compose_schemas(*schemas)
        for name, attr in attrs.items():
            fieldname = self.attributes_field + '::' + name
            atype = attr.attr_type
            args = {'label': attr.long_name, 'required': False}
            field = form_field_from_name(atype.form_field)
            # if atype.form_field == 'CharField':
            #     args['max_length'] = 32
            if (atype.form_field == 'ChoiceField' or
               atype.form_field == 'MultipleChoiceField'):
                if attr.choice_labels is not None and attr.choice_labels != []:
                    chs = list(zip(attr.choices, attr.choice_labels))
                else:
                    chs = list(map(lambda c: (c, c), attr.choices))
                args['choices'] = chs
            if atype.form_field == 'BooleanField':
                args['required'] = False
                self.set_default(args, attr, boolean=True)
            elif attr.required:
                args['required'] = True
                self.set_default(args, attr)
            else:
                self.set_default(args, attr)
            self.set_initial(args, name, attr, attrvals)
            self.fields[fieldname] = field(**args)

    def set_default(self, args, attr, boolean=False):
        if len(attr.default) > 0:
            if boolean:
                args['initial'] = (attr.default != 'False')
            else:
                args['initial'] = attr.default

    def set_initial(self, args, name, attr, attrvals):
        if name in attrvals:
            if attr.attr_type.form_field == 'BooleanField':
                args['initial'] = (
                    attrvals[name]
                    if isinstance(attrvals[name], bool)
                    else attrvals[name] != 'False'
                )
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
        setattr(self.instance, self.attributes_field, attrvals)

    def save(self, *args, **kwargs):
        if self.attributes_field is not None:
            self.process_attributes_fields()
        return super().save(*args, **kwargs)
