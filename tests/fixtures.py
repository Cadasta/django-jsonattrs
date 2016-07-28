import itertools

from django.contrib.contenttypes.models import ContentType

from jsonattrs.models import Schema, Attribute, AttributeType
from jsonattrs.management.commands import loadattrtypes

from .models import Organization, Project, Party
from .factories import (
    OrganizationFactory, ProjectFactory, ParcelFactory
)


DEFAULT_SCHEMATA = [
    {'name': 'org-default',
     'content_type': 'organization',
     'selectors': (),
     'fields': [
         {'name': 'home_office',
          'long_name': 'Country of organization home office',
          'attr_type': 'text',  # 'subtype': 'country',
          'default': 'New York', 'required': True}
     ]},

    {'name': 'prj-default',
     'content_type': 'project',
     'selectors': (),
     'fields': [
         {'name': 'head', 'long_name': 'Project head', 'attr_type': 'text'}
     ]},

    {'name': 'party-default',
     'content_type': 'party',
     'selectors': (),
     'fields': [
         {'name': 'dob', 'long_name': 'Date of birth',
          'attr_type': 'date', 'required': True},
         {'name': 'gender', 'long_name': 'Gender', 'attr_type': 'text'}
     ]},

    {'name': 'parcel-default',
     'content_type': 'parcel',
     'selectors': (),
     'fields': [
         {'name': 'quality', 'long_name': 'Quality of parcel geomeatry',
          'attr_type': 'select_one', 'default': 'none', 'required': True,
          'choices': ['none', 'text', 'point', 'polygon_low', 'polygon_high']}
     ]}
]

SPECIFIC_SCHEMATA = [
    {'name': 'party-org1',
     'content_type': 'party',
     'selectors': ('Organization #1',),
     'fields': [
         {'name': 'education', 'long_name': 'Education level',
          'attr_type': 'text'}
     ]},
    {'name': 'party-proj11',
     'content_type': 'party',
     'selectors': ('Organization #1', 'Project #1.1'),
     'fields': [
         {'name': 'homeowner', 'long_name': 'Is homeowner',
          'attr_type': 'boolean', 'required': True, 'default': False}
     ]},
    {'name': 'party-proj12',
     'content_type': 'party',
     'selectors': ('Organization #1', 'Project #1.2'),
     'fields': [
         {'name': 'homeowner', 'long_name': 'Is homeowner',
          'attr_type': 'boolean', 'required': True, 'default': False},
         {'name': 'dob', 'attr_type': 'date', 'omit': True}
     ]}
]


def create_fixtures(do_schemas=True):
    objres = {}
    schres = {}

    if do_schemas:
        loadattrtypes.run()
        schres.update(create_schema_fixtures(DEFAULT_SCHEMATA))

    for iorg in range(1, 4):
        org = OrganizationFactory.create(name='Organization #{}'.format(iorg))
        objres['org{}'.format(iorg)] = org

        for iprj in range(1, 4):
            proj = ProjectFactory.create(
                name='Project #{}.{}'.format(iorg, iprj),
                organization=org
            )
            objres['proj{}{}'.format(iorg, iprj)] = proj

    if do_schemas:
        schres.update(create_schema_fixtures(SPECIFIC_SCHEMATA))

    for iorg in range(1, 4):
        org = Organization.objects.get(name='Organization #{}'.format(iorg))

        for iprj in range(1, 4):
            proj = Project.objects.get(
                name='Project #{}.{}'.format(iorg, iprj)
            )

            for ient in range(1, 6):
                parcel = ParcelFactory.create(
                    address='Parcel #{}.{}.{}'.format(iorg, iprj, ient),
                    project=proj
                )
                objres['parcel{}{}{}'.format(iorg, iprj, ient)] = parcel

                attrs = {}
                if iorg == 1 and iprj == 1 and do_schemas:
                    attrs = {'dob': '1975-11-06'}
                party = Party.objects.create(
                    name='Party #{}.{}.{}'.format(iorg, iprj, ient),
                    project=proj, attrs=attrs
                )
                objres['party{}{}{}'.format(iorg, iprj, ient)] = party

    for m in ['organization', 'project', 'party', 'parcel']:
        objres[m + '_t'] = ContentType.objects.get(app_label='tests', model=m)

    if do_schemas:
        return objres, schres
    else:
        return objres


def selector_lookup(s):
    if s.startswith('Organization'):
        return Organization.objects.get(name=s).pk
    elif s.startswith('Project'):
        return Project.objects.get(name=s).pk
    else:
        raise ValueError('Oops.  Bad selector in schema fixture!')


def create_schema_fixtures(schemata):
    res = {}

    for schema in schemata:
        selectors = []
        for s in schema['selectors']:
            selectors.append(selector_lookup(s))
        schema_obj = Schema.objects.create(
            content_type=ContentType.objects.get(app_label='tests',
                                                 model=schema['content_type']),
            selectors=tuple(selectors)
        )
        res[schema['name']] = schema_obj
        for field, index in zip(schema['fields'], itertools.count(1)):
            long_name = field.get('long_name', field['name'])
            attr_type = AttributeType.objects.get(name=field['attr_type'])
            choices = field.get('choices', [])
            default = field.get('default', '')
            required = field.get('required', False)
            omit = field.get('omit', False)
            Attribute.objects.create(
                schema=schema_obj,
                name=field['name'], long_name=long_name,
                attr_type=attr_type, index=index,
                choices=choices, default=default,
                required=required, omit=omit
            )

    return res


def create_labelled_schema(label, field_mod=None):
    content_type = ContentType.objects.get(app_label='tests', model='labelled')
    schema = Schema.objects.create(
        content_type=content_type, selectors=(label,)
    )
    text_type = AttributeType.objects.get(name='text')
    int_type = AttributeType.objects.get(name='integer')
    fields = {}
    fields['f1'] = {'attr_type': text_type}
    fields['f2'] = {'attr_type': text_type, 'required': True}
    fields['f3'] = {'attr_type': int_type}
    fields['f4'] = {'attr_type': text_type,
                    'choices': ('abc', 'def', 'ghi', 'jkl')}
    if field_mod == '-f1':
        del fields['f1']
    elif field_mod == '-f2':
        del fields['f2']
    elif field_mod == '+f5-nonreq':
        fields['f5'] = {'attr_type': text_type}
    elif field_mod == '+f5-req-no-default':
        fields['f5'] = {'attr_type': text_type, 'required': True}
    elif field_mod == '+f5-req-default':
        fields['f5'] = {'attr_type': text_type, 'required': True,
                        'default': 'default'}
    elif field_mod == 'f3-text':
        fields['f3']['attr_type'] = text_type
    elif field_mod == 'f2-int':
        fields['f2']['attr_type'] = int_type
    elif field_mod == 'f4-remove-choices':
        del fields['f4']['choices']
    elif field_mod == 'f1-add-choices':
        fields['f1']['choices'] = ('ABC', 'DEF', 'GHI', 'JKL')
    elif field_mod == 'f4-change-choices':
        fields['f4']['choices'] = ('ghi', 'jkl', 'mno', 'pqr')
    idx = 1
    for n, f in fields.items():
        args = {}
        args['schema'] = schema
        args['name'] = n
        args['long_name'] = n
        args['index'] = idx
        idx += 1
        args['attr_type'] = f['attr_type']
        if 'required' in f:
            args['required'] = f['required']
        if 'default' in f:
            args['default'] = f['default']
        if 'choices' in f:
            args['choices'] = f['choices']
        Attribute.objects.create(**args)


def create_labelled_schemata():
    loadattrtypes.run()

    # Initial schema:
    #  f1: non-required string field
    #  f2: required string field
    #  f3: non-required integer field
    #  f4: choices field ('abc', 'def', 'ghi', 'jkl')
    create_labelled_schema('initial')

    # Remove non-required field schema:
    #  f2: required string field
    #  f3: non-required integer field
    #  f4: choices field ('abc', 'def', 'ghi', 'jkl')
    create_labelled_schema('remove_non_required', '-f1')

    # Remove required field schema:
    #  f1: non-required string field
    #  f3: non-required integer field
    #  f4: choices field ('abc', 'def', 'ghi', 'jkl')
    create_labelled_schema('remove_required', '-f2')

    # Add new non-required field schema:
    #  f1: non-required string field
    #  f2: required string field
    #  f3: non-required integer field
    #  f4: choices field ('abc', 'def', 'ghi', 'jkl')
    #  f5: non-required integer field
    create_labelled_schema('new_non_required', '+f5-nonreq')

    # Add new required field (no default) schema:
    #  f1: non-required string field
    #  f2: required string field
    #  f3: non-required integer field
    #  f4: choices field ('abc', 'def', 'ghi', 'jkl')
    #  f5: required integer field (no default)
    create_labelled_schema('new_required_no_default', '+f5-req-no-default')

    # Add new required field (default) schema:
    #  f1: non-required string field
    #  f2: required string field
    #  f3: non-required integer field
    #  f4: choices field ('abc', 'def', 'ghi', 'jkl')
    #  f5: required integer field (default)
    create_labelled_schema('new_required_default', '+f5-req-default')

    # Change field type (compatible) schema:
    #  f1: non-required string field
    #  f2: required string field
    #  f3: non-required string field
    #  f4: choices field ('abc', 'def', 'ghi', 'jkl')
    create_labelled_schema('type_compatible', 'f3-text')

    # Change field type (incompatible) schema:
    #  f1: non-required string field
    #  f2: required integer field
    #  f3: non-required integer field
    #  f4: choices field ('abc', 'def', 'ghi', 'jkl')
    create_labelled_schema('type_incompatible', 'f2-int')

    # Remove choices list schema:
    #  f1: non-required string field
    #  f2: required integer field
    #  f3: non-required integer field
    #  f4: non-required string field
    create_labelled_schema('remove_choices', 'f4-remove-choices')

    # Add choices list schema:
    #  f1: choices field ('ABC', 'DEF', 'GHI', 'JKL')
    #  f2: required integer field
    #  f3: non-required integer field
    #  f4: choices field ('abc', 'def', 'ghi', 'jkl')
    create_labelled_schema('add_choices', 'f1-add-choices')

    # Change choices list schema:
    #  f1: non-required string field
    #  f2: required integer field
    #  f3: non-required integer field
    #  f4: choices field ('ghi', 'jkl', 'mno', 'pqr')
    create_labelled_schema('change_choices', 'f4-change-choices')
