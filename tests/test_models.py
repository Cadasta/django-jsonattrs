from collections import OrderedDict
from django.test import TestCase
from unittest.mock import patch, MagicMock

from jsonattrs.models import Schema, Attribute, AttributeType, compose_schemas
from .fixtures import create_fixtures


class ComposeSchemaTest(TestCase):
    def setUp(self):
        self.fixtures = create_fixtures(do_schemas=False, load_attr_types=True)
        self.schema = Schema.objects.create(
            content_type=self.fixtures['party_t'], selectors=()
        )
        self.attr_type = AttributeType.objects.get(name='select_one')

    @patch('jsonattrs.models.caches')
    def test_compose_schemas_cache_deserialize(self, mock_caches):
        attr1, attr2 = Attribute.objects.bulk_create(Attribute(
            id=i,
            schema_id=self.schema.id,
            name='testattr%s' % i,
            long_name='Test attribute%s' % i,
            index=i,
            attr_type_id=self.attr_type.id,
            required=bool(i % 2),
            default=i**i if not bool(i % 2) else '') for i in range(1, 3)
        )
        cache_value = (
            OrderedDict([
                ('testattr1', attr1.to_dict()),
                ('testattr2', attr2.to_dict())
            ]),
            {'testattr1'},
            {'testattr2'}
        )
        mock_cache = MagicMock(get=MagicMock(return_value=cache_value))
        mock_caches.__getitem__.return_value = mock_cache

        assert compose_schemas(self.schema) == (
            OrderedDict([
                ('testattr1', attr1),
                ('testattr2', attr2)
            ]),
            {'testattr1'},
            {'testattr2'}
        )
        assert not mock_cache.set.called

    @patch('jsonattrs.models.caches')
    def test_compose_schemas_cache_serialize(self, mock_caches):
        mock_cache = MagicMock(get=MagicMock(return_value=None))
        mock_caches.__getitem__.return_value = mock_cache

        attr1, attr2 = Attribute.objects.bulk_create(Attribute(
            id=i,
            schema_id=self.schema.id,
            name='testattr%s' % i,
            long_name='Test attribute%s' % i,
            index=i,
            attr_type_id=self.attr_type.id,
            required=bool(i % 2),
            default=i**i if not bool(i % 2) else '') for i in range(1, 3)
        )
        attr1.refresh_from_db()
        attr2.refresh_from_db()

        assert compose_schemas(self.schema) == (
            OrderedDict([
                ('testattr1', attr1),
                ('testattr2', attr2)
            ]),
            {'testattr1'},
            {'testattr2'}
        )
        mock_cache.set.assert_called_once_with(
            'jsonattrs:compose:{}'.format(self.schema.id),
            (
                OrderedDict([
                    ('testattr1', attr1.to_dict()),
                    ('testattr2', attr2.to_dict())
                ]),
                {'testattr1'},
                {'testattr2'}
            )
        )

    def test_serialize_deserialize(self):
        attr = Attribute.objects.create(
            schema_id=self.schema.id,
            name='testattr',
            long_name='Test attribute',
            index=1,
            attr_type_id=self.attr_type.id,
        )
        assert Attribute(**attr.to_dict()) == attr

    def test_str(self):
        attr = Attribute(name='testattr', id=123)
        assert str(attr) == '<Attribute #123: name=testattr>'
        assert repr(attr) == '<Attribute #123: name=testattr>'
