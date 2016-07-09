from django.test import TestCase
from django.views.generic import TemplateView

from django.contrib.contenttypes.models import ContentType
from jsonattrs import models, mixins

from . import factories


class JsonAttrsView(mixins.JsonAttrsMixin, TemplateView):
    attributes_field = 'attrs'


class JsonAttrsMixinTest(TestCase):
    def test_get_context(self):
        models.create_attribute_types()
        org = factories.OrganizationFactory.create()
        project = factories.ProjectFactory.create(organization=org)
        content_type = ContentType.objects.get(
            app_label='tests', model='party')

        schema1 = models.Schema.objects.create(
            content_type=content_type,
            selectors=(org.id, project.id))

        models.Attribute.objects.create(
            schema=schema1,
            name='field_1',
            long_name='Field 1',
            attr_type=models.AttributeType.objects.get(name='text'),
            index=0
        )
        models.Attribute.objects.create(
            schema=schema1,
            name='field_2',
            long_name='Field 2',
            attr_type=models.AttributeType.objects.get(name='text'),
            index=1
        )

        party = factories.PartyFactory.create(
            project=project,
            attrs={'field_1': 'Some value'}
        )

        view = JsonAttrsView()
        view.object = party
        context = view.get_context_data()
        assert len(context['attrs']) == 2

        assert context['attrs'][0] == ('Field 1', 'Some value')
        assert context['attrs'][1] == ('Field 2', '—')
