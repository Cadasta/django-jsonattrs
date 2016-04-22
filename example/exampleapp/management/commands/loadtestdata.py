from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType


DATA = [
    {'type': 'division',
     'args': {'name': 'Civil'},
     'sub_objects': [
         {'type': 'department',
          'args': {'name': 'Buildings'},
          'sub_objects': [
              {'type': 'party', 'args': {'name': 'Ian'}},
              {'type': 'party', 'args': {'name': 'Rita'}},
              {'type': 'contract', 'args': {}},
              {'type': 'contract', 'args': {}},
              {'type': 'contract', 'args': {}}
          ]},
         {'type': 'department',
          'args': {'name': 'Bridges'},
          'sub_objects': [
              {'type': 'party', 'args': {'name': 'Frank'}},
              {'type': 'party', 'args': {'name': 'Boris'}},
              {'type': 'contract', 'args': {}},
              {'type': 'contract', 'args': {}},
          ]},
         {'type': 'department',
          'args': {'name': 'Tunnels'},
          'sub_objects': [
              {'type': 'party', 'args': {'name': 'Kate'}},
              {'type': 'party', 'args': {'name': 'Noel'}},
              {'type': 'contract', 'args': {}},
              {'type': 'contract', 'args': {}},
              {'type': 'contract', 'args': {}}
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
              {'type': 'contract', 'args': {}},
              {'type': 'contract', 'args': {}},
              {'type': 'contract', 'args': {}}
          ]},
         {'type': 'department',
          'args': {'name': 'Pipelines'},
          'sub_objects': [
              {'type': 'party', 'args': {'name': 'Annie Angelfish'}},
              {'type': 'party', 'args': {'name': 'Ollie Orca'}},
              {'type': 'party', 'args': {'name': 'Suzie Skate'}},
              {'type': 'contract', 'args': {}},
              {'type': 'contract', 'args': {}}
          ]},
     ]}
]


def delete_object(typ, args, parent_typ, parent_obj):
    typ.model_class().objects.filter(**args).delete()


def create_object(typ, args, parent_typ, parent_obj):
    print('create_object: typ =', typ, ' args =', args,
          ' parent_typ =', parent_typ,
          ' parent_obj =', parent_obj)
    if parent_typ is not None:
        return typ.model_class().objects.create(
            **args, **{parent_typ: parent_obj}
        )
    else:
        return typ.model_class().objects.create(**args)


def process(action, data, parent_typ=None, parent_obj=None):
    for obj in data:
        typ = ContentType.objects.get(
            app_label='exampleapp', model=obj['type']
        )
        new_obj = action(typ, obj['args'], parent_typ, parent_obj)
        if 'sub_objects' in obj:
            process(action, obj['sub_objects'], obj['type'], new_obj)


class Command(BaseCommand):
    help = "Load test data for example application."

    def add_arguments(self, parser):
        parser.add_argument(
            '--delete', action='store_true', dest='delete', default=False,
            help="Delete the test data."
        )

    def handle(self, *args, **options):
        if options['delete']:
            process(delete_object, DATA)
        else:
            process(create_object, DATA)
