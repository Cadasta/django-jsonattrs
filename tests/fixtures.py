import itertools

from django.contrib.contenttypes.models import ContentType

from jsonattrs.models import Schema, Attribute

from .models import Organization, Project
from .factories import (
    OrganizationFactory, ProjectFactory, PartyFactory, ParcelFactory
)


DEFAULT_SCHEMATA = [
    {'name': 'org-default',
     'content_type': 'organization',
     'selectors': (),
     'fields': [
         {'name': 'home_office',
          'long_name': 'Country of organization home office',
          'coarse_type': 'CharField', 'subtype': 'country',
          'default': 'New York', 'required': True}
     ]},

    {'name': 'prj-default',
     'content_type': 'project',
     'selectors': (),
     'fields': [
         {'name': 'head', 'long_name': 'Project head',
          'coarse_type': 'CharField'}
     ]},

    {'name': 'party-default',
     'content_type': 'party',
     'selectors': (),
     'fields': [
         {'name': 'dob', 'long_name': 'Date of birth',
          'coarse_type': 'DateField'},
         {'name': 'gender', 'long_name': 'Gender',
          'coarse_type': 'CharField'}
     ]},

    {'name': 'parcel-default',
     'content_type': 'parcel',
     'selectors': (),
     'fields': [
         {'name': 'quality', 'long_name': 'Quality of parcel geomeatry',
          'coarse_type': 'CharField', 'default': 'none', 'required': True,
          'choices': 'none,text,point,polygon_low,polygon_high'}
     ]}
]

SPECIFIC_SCHEMATA = [
    {'name': 'party-org1',
     'content_type': 'party',
     'selectors': ('Organization #1',),
     'fields': [
         {'name': 'education', 'long_name': 'Education level',
          'coarse_type': 'CharField'}
     ]},
    {'name': 'party-proj11',
     'content_type': 'party',
     'selectors': ('Organization #1', 'Project #1.1'),
     'fields': [
         {'name': 'homeowner', 'long_name': 'Is homeowner',
          'coarse_type': 'BooleanField', 'required': True,
          'default': False}
     ]},
    {'name': 'party-proj12',
     'content_type': 'party',
     'selectors': ('Organization #1', 'Project #1.2'),
     'fields': [
         {'name': 'homeowner', 'long_name': 'Is homeowner',
          'coarse_type': 'BooleanField', 'required': True,
          'default': False},
         {'name': 'dob', 'omit': True}
     ]}
]


def create_fixtures(do_schemas=True):
    objres = {}
    schres = {}

    if do_schemas:
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

                party = PartyFactory.create(
                    name='Party #{}.{}.{}'.format(iorg, iprj, ient),
                    project=proj
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
            long_name = field.get('long_name', '')
            coarse_type = field.get('coarse_type', '')
            subtype = field.get('subtype', '')
            choices = field.get('choices', '')
            default = field.get('default', '')
            required = field.get('required', False)
            omit = field.get('omit', False)
            Attribute.objects.create(
                schema=schema_obj,
                name=field['name'], long_name=long_name,
                coarse_type=coarse_type, subtype=subtype,
                index=index,
                choices=choices, default=default,
                required=required, omit=omit
            )

    return res
