from django.test import TestCase

from .models import Organization, Project, Party, Parcel
from .fixtures import create_fixtures


class FixtureTest(TestCase):
    def setUp(self):
        create_fixtures()

    def test_fixtures(self):
        assert Organization.objects.count() == 3
        assert Project.objects.count() == 9
        assert Parcel.objects.count() == 45
        assert Party.objects.count() == 45
