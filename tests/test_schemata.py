import pytest
from django.test import TestCase
from django.db.utils import IntegrityError

from jsonattrs.models import Schema

from .fixtures import create_fixtures


class SchemataTest(TestCase):
    def setUp(self):
        self.fixtures = create_fixtures(False)

    def test_schema_str(self):
        org = self.fixtures['org1'].name
        prj = self.fixtures['proj11'].name
        schema1 = Schema.objects.create(
            content_type=self.fixtures['party_t'],
            selectors=()
        )
        assert str(schema1) == '<Schema #{}: party+()>'.format(schema1.pk)
        assert repr(schema1) == '<Schema #{}: party+()>'.format(schema1.pk)
        schema2 = Schema.objects.create(
            content_type=self.fixtures['party_t'],
            selectors=(org,)
        )
        assert (str(schema2) ==
                "<Schema #{}: party+('{}',)>".format(schema2.pk, org))
        assert (repr(schema2) ==
                "<Schema #{}: party+('{}',)>".format(schema2.pk, org))
        schema3 = Schema.objects.create(
            content_type=self.fixtures['party_t'],
            selectors=(org, prj)
        )
        assert (str(schema3) ==
                "<Schema #{}: party+('{}', '{}')>".format(schema3.pk,
                                                          org, prj))
        assert (repr(schema3) ==
                "<Schema #{}: party+('{}', '{}')>".format(schema3.pk,
                                                          org, prj))

    def test_manual_schema_setup(self):
        schema = Schema.objects.create(
            content_type=self.fixtures['party_t'],
            selectors=(self.fixtures['org1'].name,
                       self.fixtures['proj11'].name)
        )
        assert schema.content_type == self.fixtures['party_t']
        assert tuple(schema.selectors) == (self.fixtures['org1'].name,
                                           self.fixtures['proj11'].name)

    def _create_test_schemata(self):
        party = self.fixtures['party_t']
        parcel = self.fixtures['parcel_t']
        o1 = self.fixtures['org1'].name
        o2 = self.fixtures['org2'].name
        p11 = self.fixtures['proj11'].name
        p12 = self.fixtures['proj12'].name
        p21 = self.fixtures['proj21'].name
        s1 = Schema.objects.create(content_type=party, selectors=(o1, p11))
        s2 = Schema.objects.create(content_type=parcel, selectors=(o1, p11))
        s3 = Schema.objects.create(content_type=party, selectors=(o1, p12))
        s4 = Schema.objects.create(content_type=party, selectors=(o2, p21))
        s5 = Schema.objects.create(content_type=party, selectors=(o2,))
        s6 = Schema.objects.create(content_type=party, selectors=())
        return s1, s2, s3, s4, s5, s6

    def test_schema_unique_together_ok(self):
        for s in self._create_test_schemata():
            s.full_clean()

    def test_schema_unique_together_overlap(self):
        p = self.fixtures['party_t']
        o1 = self.fixtures['org1'].name
        p11 = self.fixtures['proj11'].name
        Schema.objects.create(content_type=p, selectors=(o1, p11)).full_clean()
        Schema.objects.create(content_type=p, selectors=(o1,)).full_clean()
        Schema.objects.create(content_type=p, selectors=()).full_clean()
        with pytest.raises(IntegrityError):
            Schema.objects.create(content_type=p, selectors=(o1, p11))

    def test_schema_deletion(self):
        before_count = Schema.objects.count()
        test_schema = Schema.objects.create(
            content_type=self.fixtures['party_t'],
            selectors=(self.fixtures['org1'].name,
                       self.fixtures['proj11'].name)
        )
        test_schema.delete()
        assert Schema.objects.count() == before_count

    def test_schema_lookup(self):
        s1, s2, s3, s4, s5, s6 = self._create_test_schemata()
        party = self.fixtures['party_t']
        parcel = self.fixtures['parcel_t']
        o1 = self.fixtures['org1'].name
        o2 = self.fixtures['org2'].name
        p11 = self.fixtures['proj11'].name
        p12 = self.fixtures['proj12'].name
        p21 = self.fixtures['proj21'].name

        def check(ct, sels, val):
            assert list(Schema.objects.filter(content_type=ct,
                                              selectors=sels)) == [val]

        check(party, (o1, p11), s1)
        check(parcel, (o1, p11), s2)
        check(party, (o1, p12), s3)
        check(party, (o2, p21), s4)
        check(party, (o2,), s5)
        check(party, (), s6)
