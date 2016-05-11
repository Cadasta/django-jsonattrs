import itertools

from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType

from jsonattrs.models import Schema, Attribute
from exampleapp.models import Division, Department, Party


DATA = [
    {'type': 'division',
     'args': {'name': 'Civil'},
     'sub_objects': [
         {'type': 'department',
          'args': {'name': 'Buildings'},
          'sub_objects': [
              {'type': 'party', 'args': {'name': 'Ian'}},
              {'type': 'party', 'args': {'name': 'Rita'}},
              {'type': 'contract', 'args': {'responsible': 'Ian'}},
              {'type': 'contract', 'args': {'responsible': 'Rita'}},
              {'type': 'contract', 'args': {'responsible': 'Rita'}}
          ]},
         {'type': 'department',
          'args': {'name': 'Bridges'},
          'sub_objects': [
              {'type': 'party', 'args': {'name': 'Frank'}},
              {'type': 'party', 'args': {'name': 'Boris'}},
              {'type': 'contract', 'args': {'responsible': 'Frank'}},
              {'type': 'contract', 'args': {'responsible': 'Boris'}},
          ]},
         {'type': 'department',
          'args': {'name': 'Tunnels'},
          'sub_objects': [
              {'type': 'party', 'args': {'name': 'Kate'}},
              {'type': 'party', 'args': {'name': 'Noel'}},
              {'type': 'contract', 'args': {'responsible': 'Kate'}},
              {'type': 'contract', 'args': {'responsible': 'Kate'}},
              {'type': 'contract', 'args': {'responsible': 'Noel'}}
          ]}
     ]},
    {'type': 'division',
     'args': {'name': 'Marine'},
     'sub_objects': [
         {'type': 'department',
          'args': {'name': 'Platforms'},
          'sub_objects': [
              {'type': 'party', 'args': {'name': 'Steve Squid'}},
              {'type': 'party', 'args': {'name': 'Nellie Nautilus'}},
              {'type': 'contract', 'args': {'responsible': 'Nellie Nautilus'}},
              {'type': 'contract', 'args': {'responsible': 'Nellie Nautilus'}},
              {'type': 'contract', 'args': {'responsible': 'Nellie Nautilus'}}
          ]},
         {'type': 'department',
          'args': {'name': 'Pipelines'},
          'sub_objects': [
              {'type': 'party', 'args': {'name': 'Annie Angelfish'}},
              {'type': 'party', 'args': {'name': 'Ollie Orca'}},
              {'type': 'party', 'args': {'name': 'Suzie Skate'}},
              {'type': 'contract', 'args': {'responsible': 'Suzie Skate'}},
              {'type': 'contract', 'args': {'responsible': 'Suzie Skate'}}
          ]},
     ]}
]


def named_content_type(name):
    return ContentType.objects.get(app_label='exampleapp', model=name)


def delete_object(typ, args, parent_typ, parent_obj):
    try:
        if 'responsible' in args:
            args['responsible'] = Party.objects.get(name=args['responsible'])
        typ.model_class().objects.filter(**args).delete()
    except ObjectDoesNotExist:
        pass


def create_object(typ, args, parent_typ, parent_obj):
    print('create_object: typ =', typ, ' args =', args,
          ' parent_typ =', parent_typ,
          ' parent_obj =', parent_obj)
    if 'responsible' in args:
        args['responsible'] = Party.objects.get(name=args['responsible'])
    if parent_typ is not None:
        return typ.model_class().objects.create(
            **args, **{parent_typ: parent_obj}
        )
    else:
        return typ.model_class().objects.create(**args)


def process_data(action, data, parent_typ=None, parent_obj=None):
    for obj in data:
        typ = named_content_type(obj['type'])
        new_obj = action(typ, obj['args'], parent_typ, parent_obj)
        if 'sub_objects' in obj:
            process_data(action, obj['sub_objects'], obj['type'], new_obj)


SCHEMATA = [
    {'content_type': 'division',
     'selectors': (),
     'fields': [
         {'name': 'turnover', 'long_name': 'Total divisional turnover',
          'coarse_type': 'IntField', 'subtype': 'currency'}
     ]},

    {'content_type': 'department',
     'selectors': (),
     'fields': [
         {'name': 'chief', 'long_name': 'Department chief',
          'coarse_type': 'CharField', 'subtype': 'foreign-key(Party)'}
     ]},

    {'content_type': 'party',
     'selectors': (),
     'fields': [
         {'name': 'office', 'long_name': 'City of base office',
          'coarse_type': 'CharField', 'subtype': 'city', 'required': True},
         {'name': 'salary', 'long_name': 'Employee salary',
          'coarse_type': 'IntField', 'subtype': 'currency'}
     ]},
    {'content_type': 'party',
     'selectors': ('Civil',),
     'fields': [
         {'name': 'digger', 'long_name': 'Can dig!',
          'coarse_type': 'BooleanField', 'required': True},
         {'name': 'certification', 'long_name': 'CEng certification level',
          'coarse_type': 'ChoiceField',
          'choices': 'None,Apprentice,Journeyman,Master', 'default': 'None',
          'required': True}
     ]},
    {'content_type': 'party',
     'selectors': ('Civil', 'Bridges'),
     'fields': [
         {'name': 'vertigo', 'long_name': 'Gets vertigo',
          'coarse_type': 'BooleanField', 'required': True}
     ]},
    {'content_type': 'party',
     'selectors': ('Marine',),
     'fields': [
         {'name': 'aquatic', 'long_name': 'Can breathe underwater!',
          'coarse_type': 'BooleanField', 'required': True}
     ]},

    {'content_type': 'contract',
     'selectors': (),
     'fields': [
         {'name': 'jurisdiction', 'long_name': 'Legal jurisdiction',
          'coarse_type': 'CharField', 'subtype': 'country', 'required': True}
     ]}
]


def selectors_from_names(selector_names):
    div = None
    dept = None
    if len(selector_names) > 0:
        div = Division.objects.get(name=selector_names[0])
    if len(selector_names) > 1:
        dept = Department.objects.get(name=selector_names[1])
    if div is not None and dept is not None:
        return (div, dept)
    elif div is not None:
        return (div,)
    else:
        return ()


def delete_schemata():
    for schema in SCHEMATA:
        try:
            print('Deleting schema:',
                  schema['content_type'], schema['selectors'])
            Schema.objects.by_selectors(
                content_type=named_content_type(schema['content_type']),
                selectors=selectors_from_names(schema['selectors'])
            ).delete()
        except ObjectDoesNotExist:
            print('Failed deleting schema:', schema)
            pass


def create_schemata():
    for schema in SCHEMATA:
        print('Creating schema:', schema['content_type'], schema['selectors'])
        schema_obj = Schema.objects.create(
            content_type=named_content_type(schema['content_type']),
            selectors=selectors_from_names(schema['selectors'])
        )
        for field, index in zip(schema['fields'], itertools.count(1)):
            subtype = field.get('subtype', '')
            choices = field.get('choices', '')
            default = field.get('default', '')
            required = field.get('required', False)
            omit = field.get('omit', False)
            Attribute.objects.create(
                schema=schema_obj,
                name=field['name'], long_name=field['long_name'],
                coarse_type=field['coarse_type'], subtype=subtype,
                index=index,
                choices=choices, default=default,
                required=required, omit=omit
            )


class Command(BaseCommand):
    help = "Load test data for example application."

    def add_arguments(self, parser):
        parser.add_argument(
            '--delete', action='store_true', dest='delete', default=False,
            help="Delete the test data."
        )

    def handle(self, *args, **options):
        if options['delete']:
            delete_schemata()
            process_data(delete_object, DATA)
        else:
            process_data(create_object, DATA)
            create_schemata()
