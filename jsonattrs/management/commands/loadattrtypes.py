from django.core.management.base import BaseCommand

from jsonattrs.models import AttributeType, create_attribute_type


def create_attribute_types():
    create_attribute_type('boolean', 'Boolean', 'BooleanField',
                          validator_type='bool',
                          validator_re=r'true|false|True|False')

    create_attribute_type('text', 'Text', 'CharField',
                          validator_type='str')
    create_attribute_type('text_multiline', 'Multiline text', 'CharField',
                          validator_type='str',
                          widget='Textarea')

    create_attribute_type('date', 'Date', 'DateField')
    create_attribute_type('dateTime', 'Date and time', 'DateTimeField')
    create_attribute_type('time', 'Time', 'TimeField')

    create_attribute_type('integer', 'Integer', 'IntegerField',
                          validator_re=r'[-+]?\d+')
    create_attribute_type('decimal', 'Decimal number', 'DecimalField',
                          validator_re=r'[-+]?\d+(\.\d+)?')

    create_attribute_type('email', 'Email address', 'EmailField')
    create_attribute_type('url', 'URL', 'URLField')

    create_attribute_type('select_one', 'Select one:', 'ChoiceField')
    create_attribute_type('select_multiple', 'Select multiple:',
                          'MultipleChoiceField')
    create_attribute_type('foreign_key', 'Select one:', 'ModelChoiceField')


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
