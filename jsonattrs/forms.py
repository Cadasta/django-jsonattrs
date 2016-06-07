from django import forms
from django.contrib.contenttypes.models import ContentType

from .models import Schema, compose_schemas


class AttributeModelForm(forms.ModelForm):
    attributes_field = None

    def __init__(self, schema_selectors=None, *args, **kwargs):
        print('AttributeModelForm.__init__')
        super().__init__(*args, **kwargs)
        if self.attributes_field is not None:
            self.add_attribute_fields(schema_selectors)

    def add_attribute_fields(self, schema_selectors):
        print('AttributeModelForm.add_attribute_fields')
        attrs = None
        schemas = None
        if hasattr(self, 'instance') and self.instance is not None:
            schemas = Schema.objects.from_instance(self.instance)
        elif schema_selectors is not None:
            content_type = ContentType.objects.get_for_model(self.model)
            schemas = Schema.objects.lookup(
                content_type, schema_selectors
            )
        attrs, _, _ = compose_schemas(*schemas)
        for name, attr in attrs.items():
            print(name, attr.coarse_type, attr.choices)
            name = self.attributes_field + '::' + name
            field = getattr(forms, attr.coarse_type, None)
            if field is not None:
                args = {'label': attr.long_name}
                if attr.coarse_type == 'CharField':
                    args['max_length'] = 32
                if attr.coarse_type == 'ChoiceField':
                    args['choices'] = list(map(lambda c: (c, c),
                                               attr.choices.split(',')))
                if attr.coarse_type == 'BooleanField':
                    args['required'] = False
                elif attr.required:
                    args['required'] = True
                if len(attr.default) > 0:
                    args['initial'] = attr.default
                print(name, field, args)
                self.fields[name] = field(**args)
