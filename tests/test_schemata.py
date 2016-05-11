import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError

from jsonattrs.models import Schema, SchemaSelector

from .fixtures import create_object_fixtures


class SchemataTest(TestCase):
    def setUp(self):
        self.fixtures = create_object_fixtures()

    def test_schema_str(self):
        schema = Schema.objects.create(content_type=self.fixtures['party_t'])
        assert str(schema) == '<Schema #{}: party>'.format(schema.pk)
        assert repr(schema) == '<Schema #{}: party>'.format(schema.pk)

    def test_schema_selector_str(self):
        schema = Schema.objects.create(content_type=self.fixtures['party_t'])
        selector = SchemaSelector.objects.create(
            schema=schema, index=1, selector=self.fixtures['org1']
        )
        cmp = '<SchemaSelector #{} (1/1): {}>'.format(
            selector.pk, self.fixtures['org1'].name
        )
        assert str(selector) == cmp
        assert repr(selector) == cmp

    def test_manual_schema_setup(self):
        schema = Schema.objects.create(
            content_type=self.fixtures['party_t'],
            selectors=(self.fixtures['org1'], self.fixtures['proj11'])
        )
        assert (list(map(lambda ss: ss.selector, (schema.selectors.all()))) ==
                [self.fixtures['org1'], self.fixtures['proj11']])

    def _create_test_schemata(self):
        s1 = Schema.objects.create(
            content_type=self.fixtures['party_t'],
            selectors=(self.fixtures['org1'], self.fixtures['proj11'])
        )
        s2 = Schema.objects.create(
            content_type=self.fixtures['parcel_t'],
            selectors=(self.fixtures['org1'], self.fixtures['proj11'])
        )
        s3 = Schema.objects.create(
            content_type=self.fixtures['party_t'],
            selectors=(self.fixtures['org1'], self.fixtures['proj12'])
        )
        s4 = Schema.objects.create(
            content_type=self.fixtures['party_t'],
            selectors=(self.fixtures['org2'], self.fixtures['proj21'])
        )
        s5 = Schema.objects.create(
            content_type=self.fixtures['party_t'],
            selectors=(self.fixtures['org2'],)
        )
        s6 = Schema.objects.create(
            content_type=self.fixtures['party_t'],
            selectors=()
        )
        return s1, s2, s3, s4, s5, s6

    def test_schema_unique_together_ok(self):
        for s in self._create_test_schemata():
            s.full_clean()

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

    def test_schema_by_selectors(self):
        s1, s2, s3, s4, s5, s6 = self._create_test_schemata()
        party = self.fixtures['party_t']
        parcel = self.fixtures['parcel_t']
        org1 = self.fixtures['org1']
        org2 = self.fixtures['org2']
        prj11 = self.fixtures['proj11']
        prj12 = self.fixtures['proj12']
        prj21 = self.fixtures['proj21']
        assert list(Schema.objects.by_selectors(party, (org1, prj11))) == [s1]
        assert list(Schema.objects.by_selectors(parcel, (org1, prj11))) == [s2]
        assert list(Schema.objects.by_selectors(party, (org1, prj12))) == [s3]
        assert list(Schema.objects.by_selectors(party, (org2, prj21))) == [s4]
        assert list(Schema.objects.by_selectors(party, (org2,))) == [s5]
        assert list(Schema.objects.by_selectors(party, ())) == [s6]
