from django.test import TestCase

from jsonattrs.models import Schema, SchemaSelector

from .fixtures import create_fixtures


class SchemataTest(TestCase):
    def setUp(self):
        self.fixtures = create_fixtures()

    def test_schema_str(self):
        schema = Schema.objects.create(content_type=self.fixtures['party_t'])
        assert str(schema) == '<Schema #1: party>'
        assert repr(schema) == '<Schema #1: party>'

    def test_schema_selector_str(self):
        schema = Schema.objects.create(content_type=self.fixtures['party_t'])
        selector = SchemaSelector.objects.create(
            schema=schema, index=1, selector=self.fixtures['org1']
        )
        assert str(selector) == '<SchemaSelector #1 (1/1): Organization #1>'
        assert repr(selector) == '<SchemaSelector #1 (1/1): Organization #1>'

    def test_manual_schema_setup(self):
        schema = Schema.objects.create(content_type=self.fixtures['party_t'])
        selector1 = SchemaSelector.objects.create(
            schema=schema, index=1, selector=self.fixtures['org1']
        )
        selector2 = SchemaSelector.objects.create(
            schema=schema, index=2, selector=self.fixtures['proj11']
        )
        assert list(schema.selectors.all()) == [selector1, selector2]
