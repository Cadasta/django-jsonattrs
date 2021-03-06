import itertools

from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType

from jsonattrs.models import Schema, Attribute, AttributeType
from exampleapp.models import Division, Department, Party


DATA = [
    {'type': 'division',
     'first_pass': True,
     'args': {'name': 'Civil'},
     'sub_objects': [
         {'type': 'department',
          'first_pass': True,
          'args': {'name': 'Buildings'},
          'sub_objects': [
              {'type': 'party', 'args': {'name': 'Ian'}},
              {'type': 'party', 'args': {'name': 'Rita'}},
              {'type': 'contract', 'args': {'responsible': 'Ian'}},
              {'type': 'contract', 'args': {'responsible': 'Rita'}},
              {'type': 'contract', 'args': {'responsible': 'Rita'}}
          ]},
         {'type': 'department',
          'first_pass': True,
          'args': {'name': 'Bridges'},
          'sub_objects': [
              {'type': 'party', 'args': {'name': 'Frank'}},
              {'type': 'party', 'args': {'name': 'Boris'}},
              {'type': 'contract', 'args': {'responsible': 'Frank'}},
              {'type': 'contract', 'args': {'responsible': 'Boris'}},
          ]},
         {'type': 'department',
          'first_pass': True,
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
     'first_pass': True,
     'args': {'name': 'Marine'},
     'sub_objects': [
         {'type': 'department',
          'first_pass': True,
          'args': {'name': 'Platforms'},
          'sub_objects': [
              {'type': 'party', 'args': {'name': 'Steve Squid'}},
              {'type': 'party', 'args': {'name': 'Nellie Nautilus'}},
              {'type': 'contract', 'args': {'responsible': 'Nellie Nautilus'}},
              {'type': 'contract', 'args': {'responsible': 'Nellie Nautilus'}},
              {'type': 'contract', 'args': {'responsible': 'Nellie Nautilus'}}
          ]},
         {'type': 'department',
          'first_pass': True,
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


def do_process_data(first_pass, data, parent_typ=None, parent_obj=None):
    for o in data:
        typ = named_content_type(o['type'])
        opass = o.get('first_pass', False)
        newo = None
        if first_pass:
            if opass:
                newo = create_object(typ, o['args'], parent_typ, parent_obj)
                if 'sub_objects' in o:
                    do_process_data(first_pass, o['sub_objects'],
                                    o['type'], newo)
        else:
            if not opass:
                newo = create_object(typ, o['args'], parent_typ, parent_obj)
            else:
                try:
                    newo = typ.model_class().objects.get(**o['args'])
                except:
                    pass
            if 'sub_objects' in o:
                do_process_data(first_pass, o['sub_objects'], o['type'], newo)


def create_objects():
    create_schemata(DEFAULT_SCHEMATA)
    do_process_data(True, DATA)
    create_schemata(SPECIFIC_SCHEMATA)
    do_process_data(False, DATA)


DEFAULT_SCHEMATA = [
    {'content_type': 'division',
     'selectors': (),
     'fields': [
         {'name': 'turnover', 'long_name': 'Total divisional turnover',
          'attr_type': 'integer'}  # , 'subtype': 'currency'}
     ]},

    {'content_type': 'department',
     'selectors': (),
     'fields': [
         {'name': 'chief', 'long_name': 'Department chief',
          'attr_type': 'text'}
         # 'attr_type': 'foreign-key', 'subtype': 'Party'}
     ]},

    {'content_type': 'party',
     'selectors': (),
     'fields': [
         {'name': 'office', 'long_name': 'City of base office',
          'attr_type': 'text',  # , 'subtype': 'city',
          'required': True, 'default': 'New York'},
         {'name': 'salary', 'long_name': 'Employee salary',
          'attr_type': 'integer'}  # , 'subtype': 'currency'}
     ]},

    {'content_type': 'contract',
     'selectors': (),
     'fields': [
         {'name': 'jurisdiction', 'long_name': 'Legal jurisdiction',
          'attr_type': 'text',  # , 'subtype': 'country',
          'required': True, 'default': 'US'}
     ]}
]


SPECIFIC_SCHEMATA = [
    {'content_type': 'party',
     'selectors': ('Civil',),
     'fields': [
         {'name': 'digger', 'long_name': 'Can dig!',
          'attr_type': 'boolean', 'required': True, 'default': False},
         {'name': 'certification', 'long_name': 'CEng certification level',
          'attr_type': 'select_one',
          'choices': ['-', 'A', 'J', 'M'],
          'choice_labels': ['None', 'Apprentice', 'Journeyman', 'Master'],
          'required': True, 'default': '-'},
         {'name': 'availability', 'long_name': 'What days can they work?',
          'attr_type': 'select_multiple',
          'choices': ['-', 'm', 't', 'w', 't', 'f', 's', 'su'],
          'choice_labels': ['None', 'Monday', 'Tuesday', 'Wednesday', 'Thursday',
                            'Friday', 'Saturday', 'Sunday'],
          'required': False, 'default': '[-]'}
     ]},
    {'content_type': 'party',
     'selectors': ('Civil', 'Bridges'),
     'fields': [
         {'name': 'vertigo', 'long_name': 'Gets vertigo',
          'attr_type': 'boolean', 'required': True, 'default': False}
     ]},
    {'content_type': 'party',
     'selectors': ('Marine',),
     'fields': [
         {'name': 'aquatic', 'long_name': 'Can breathe underwater!',
          'attr_type': 'boolean', 'required': True, 'default': False}
     ]}
]


def selectors_from_names(selector_names):
    div = None
    dept = None
    if len(selector_names) > 0:
        div = Division.objects.get(name=selector_names[0]).pk
    if len(selector_names) > 1:
        dept = Department.objects.get(name=selector_names[1]).pk
    if div is not None and dept is not None:
        return (div, dept)
    elif div is not None:
        return (div,)
    else:
        return ()


def delete_schema(schema):
    try:
        print('Deleting schema:',
              schema['content_type'], schema['selectors'])
        Schema.objects.get(
            content_type=named_content_type(schema['content_type']),
            selectors=selectors_from_names(schema['selectors'])
        ).delete()
    except ObjectDoesNotExist:
        print('Failed deleting schema:', schema)
        pass


def delete_schemata(schemata):
    for schema in schemata:
        delete_schema(schema)


def create_schema(schema):
    print('Creating schema:', schema['content_type'], schema['selectors'])
    schema_obj = Schema.objects.create(
        content_type=named_content_type(schema['content_type']),
        selectors=selectors_from_names(schema['selectors'])
    )
    for field, index in zip(schema['fields'], itertools.count(1)):
        choices = field.get('choices', [])
        choice_labels = field.get('choice_labels', None)
        default = field.get('default', '')
        required = field.get('required', False)
        omit = field.get('omit', False)
        Attribute.objects.create(
            schema=schema_obj,
            name=field['name'], long_name=field['long_name'],
            attr_type=AttributeType.objects.get(name=field['attr_type']),
            index=index, choices=choices, choice_labels=choice_labels,
            default=default, required=required, omit=omit
        )


def create_schemata(schemata):
    for schema in schemata:
        create_schema(schema)


class Command(BaseCommand):
    help = "Load test data for example application."

    def add_arguments(self, parser):
        parser.add_argument(
            '--delete', action='store_true', dest='delete', default=False,
            help="Delete the test data."
        )

    def handle(self, *args, **options):
        if options['delete']:
            Division.objects.all().delete()
            Schema.objects.all().delete()
        else:
            create_objects()
