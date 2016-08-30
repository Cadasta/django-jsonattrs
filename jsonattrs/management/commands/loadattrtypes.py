from django.core.management.base import BaseCommand

from jsonattrs.models import AttributeType, create_attribute_types


def run(force=False):
    if force:
        AttributeType.objects.all().delete()
    create_attribute_types()


class Command(BaseCommand):
    help = "Load default attribute types."

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            dest='force',
            default=False,
            help='Force object deletion and recreation'
        )

    def handle(self, *args, **options):
        run(force=options['force'])
