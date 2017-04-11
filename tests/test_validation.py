import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from jsonattrs.models import Schema, Attribute, AttributeType

from .fixtures import create_fixtures


class ValidationTest(TestCase):
    def setUp(self):
        self.fixtures = create_fixtures(do_schemas=False, load_attr_types=True)
        self.schema = Schema.objects.create(
            content_type=self.fixtures['party_t'], selectors=()
        )

    def test_validate_empty_integer(self):
        attr = Attribute.objects.create(
            schema=self.schema,
            name='testattr',
            long_name='Test attribute',
            index=1,
            attr_type=AttributeType.objects.get(name='integer')
        )

        attr.validate('')
        # No assertion here, validation should pass without exceptions

    def test_validate_empty_integer_on_required_attribute(self):
        attr = Attribute.objects.create(
            schema=self.schema,
            name='testattr',
            long_name='Test attribute',
            index=1,
            attr_type=AttributeType.objects.get(name='integer'),
            required=True
        )
        with pytest.raises(ValidationError):
            attr.validate('')

    def test_validate_empty_decimal(self):
        attr = Attribute.objects.create(
            schema=self.schema,
            name='testattr',
            long_name='Test attribute',
            index=1,
            attr_type=AttributeType.objects.get(name='decimal')
        )

        attr.validate('')
        # No assertion here, validation should pass without exceptions

    def test_validate_empty_decimal_on_required_attribute(self):
        attr = Attribute.objects.create(
            schema=self.schema,
            name='testattr',
            long_name='Test attribute',
            index=1,
            attr_type=AttributeType.objects.get(name='decimal'),
            required=True
        )
        with pytest.raises(ValidationError):
            attr.validate('')

    def test_validate_empty_select_one(self):
        attr = Attribute.objects.create(
            schema=self.schema,
            name='testattr',
            long_name='Test attribute',
            index=1,
            attr_type=AttributeType.objects.get(name='select_one'),
            choices=['a', 'b', 'c']
        )

        attr.validate('')
        attr.validate([''])
        # No assertion here, validation should pass without exceptions

    def test_validate_empty_select_one_on_required_attribute(self):
        attr = Attribute.objects.create(
            schema=self.schema,
            name='testattr',
            long_name='Test attribute',
            index=1,
            attr_type=AttributeType.objects.get(name='select_one'),
            choices=['a', 'b', 'c'],
            required=True
        )
        with pytest.raises(ValidationError):
            attr.validate('')

    def test_validate_empty_select_multiple(self):
        attr = Attribute.objects.create(
            schema=self.schema,
            name='testattr',
            long_name='Test attribute',
            index=1,
            attr_type=AttributeType.objects.get(name='select_multiple'),
            choices=['a', 'b', 'c']
        )

        attr.validate('')
        attr.validate([''])
        # No assertion here, validation should pass without exceptions

    def test_validate_empty_select_multiple_on_required_attribute(self):
        attr = Attribute.objects.create(
            schema=self.schema,
            name='testattr',
            long_name='Test attribute',
            index=1,
            attr_type=AttributeType.objects.get(name='select_multiple'),
            choices=['a', 'b', 'c'],
            required=True
        )

        with pytest.raises(ValidationError):
            attr.validate('')
