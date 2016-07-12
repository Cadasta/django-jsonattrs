from django.core.management.base import BaseCommand

from jsonattrs.models import AttributeType, create_attribute_types


def run():
    AttributeType.objects.all().delete()
    create_attribute_types()


class Command(BaseCommand):
    help = "Load default attribute types."

    def handle(self, *args, **options):
        run()
