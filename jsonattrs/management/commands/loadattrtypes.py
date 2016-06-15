from django.core.management.base import BaseCommand

from jsonattrs.models import AttributeType, create_attribute_types


def run(delete=False):
        if delete:
            AttributeType.objects.all().delete()
        else:
            create_attribute_types()


class Command(BaseCommand):
    help = "Load default attribute types."

    def add_arguments(self, parser):
        parser.add_argument(
            '--delete', action='store_true', dest='delete', default=False,
            help="Delete all attribute types."
        )

    def handle(self, *args, **options):
        run(options['delete'])
