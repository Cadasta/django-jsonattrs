import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError

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
        schema = Schema.objects.create(
            content_type=self.fixtures['party_t'],
            selectors=(self.fixtures['org1'], self.fixtures['proj11'])
        )
        assert (list(map(lambda ss: ss.selector, (schema.selectors.all()))) ==
                [self.fixtures['org1'], self.fixtures['proj11']])

    def test_schema_unique_together_ok(self):
        Schema.objects.create(
            content_type=self.fixtures['party_t'],
            selectors=(self.fixtures['org1'], self.fixtures['proj11'])
        ).full_clean()
        Schema.objects.create(
            content_type=self.fixtures['parcel_t'],
            selectors=(self.fixtures['org1'], self.fixtures['proj11'])
        ).full_clean()
        Schema.objects.create(
            content_type=self.fixtures['party_t'],
            selectors=(self.fixtures['org1'], self.fixtures['proj12'])
        ).full_clean()
        Schema.objects.create(
            content_type=self.fixtures['party_t'],
            selectors=(self.fixtures['org2'], self.fixtures['proj21'])
        ).full_clean()
        Schema.objects.create(
            content_type=self.fixtures['party_t'],
            selectors=(self.fixtures['org2'],)
        ).full_clean()

    def test_schema_unique_together_overlap(self):
        Schema.objects.create(
            content_type=self.fixtures['party_t'],
            selectors=(self.fixtures['org1'], self.fixtures['proj11'])
        )
        test_schema1 = Schema.objects.create(
            content_type=self.fixtures['party_t'],
            selectors=(self.fixtures['org1'], self.fixtures['proj11'])
        )
        with pytest.raises(ValidationError):
            test_schema1.full_clean()
        Schema.objects.create(
            content_type=self.fixtures['party_t'],
            selectors=(self.fixtures['org1'],)
        ).full_clean()
        Schema.objects.create(
            content_type=self.fixtures['party_t'],
            selectors=()
        ).full_clean()

    def test_schema_deletion(self):
        test_schema = Schema.objects.create(
            content_type=self.fixtures['party_t'],
            selectors=(self.fixtures['org1'], self.fixtures['proj11'])
        )
        test_schema.delete()
        assert SchemaSelector.objects.count() == 0
