import itertools

from django.contrib.contenttypes.models import ContentType

from jsonattrs.models import Schema, Attribute

from .factories import (
    OrganizationFactory, ProjectFactory, PartyFactory, ParcelFactory
)


def create_object_fixtures():
    res = {}

    for iorg in range(1, 4):
        org = OrganizationFactory.create(name='Organization #{}'.format(iorg))
        res['org{}'.format(iorg)] = org

        for iprj in range(1, 4):
            proj = ProjectFactory.create(
                name='Project #{}.{}'.format(iorg, iprj),
                organization=org
            )
            res['proj{}{}'.format(iorg, iprj)] = proj

            for ient in range(1, 6):
                parcel = ParcelFactory.create(
                    address='Parcel #{}.{}.{}'.format(iorg, iprj, ient),
                    project=proj
                )
                res['parcel{}{}{}'.format(iorg, iprj, ient)] = parcel

                party = PartyFactory.create(
                    name='Party #{}.{}.{}'.format(iorg, iprj, ient),
                    project=proj
                )
                res['party{}{}{}'.format(iorg, iprj, ient)] = party

    for m in ['organization', 'project', 'party', 'parcel']:
        res[m + '_t'] = ContentType.objects.get(app_label='tests', model=m)

    return res


SCHEMATA = [
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
    {'name': 'party-org1',
     'content_type': 'party',
     'selectors': ('org1',),
     'fields': [
         {'name': 'education', 'long_name': 'Education level',
          'coarse_type': 'CharField'}
     ]},
    {'name': 'party-proj11',
     'content_type': 'party',
     'selectors': ('org1', 'proj11'),
     'fields': [
         {'name': 'owner', 'long_name': 'Is homeowner',
          'coarse_type': 'BooleanField', 'required': True,
          'default': False}
     ]},
    {'name': 'party-proj12',
     'content_type': 'party',
     'selectors': ('org1', 'proj12'),
     'fields': [
         {'name': 'owner', 'long_name': 'Is homeowner',
          'coarse_type': 'BooleanField', 'required': True,
          'default': False},
         {'name': 'dob', 'omit': True}
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


def named_content_type(name):
    return ContentType.objects.get(app_label='tests', model=name)


def create_schema_fixtures(objs):
    res = {}

    for schema in SCHEMATA:
        nsel = len(schema['selectors'])
        if nsel == 0:
            selectors = ()
        elif nsel == 1:
            selectors = (objs[schema['selectors'][0]],)
        else:
            selectors = (objs[schema['selectors'][0]],
                         objs[schema['selectors'][1]])
        schema_obj = Schema.objects.create(
            content_type=named_content_type(schema['content_type']),
            selectors=selectors
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
