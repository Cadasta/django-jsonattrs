from django.test import TestCase
from django.views.generic import TemplateView

from django.contrib.contenttypes.models import ContentType
from jsonattrs import models, mixins

from . import factories


class XLangLabelsTest(TestCase):
    def test_dict(self):
        res = mixins.template_xlang_labels({'en': 'Field 1', 'de': 'Feld 1'})
        assert 'data-label-en="Field 1"' in res
        assert 'data-label-de="Feld 1"' in res

    def test_string(self):
        assert mixins.template_xlang_labels('Field 1') == ''

    def test_none(self):
        assert mixins.template_xlang_labels(None) == ''


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
        models.Attribute.objects.create(
            schema=schema1,
            name='field_3',
            long_name='Field 3',
            attr_type=models.AttributeType.objects.get(name='select_multiple'),
            choices=['one', 'two', 'three'],
            choice_labels=['Choice 1', 'Choice 2', 'Choice 3'],
            index=2,
        )
        models.Attribute.objects.create(
            schema=schema1,
            name='field_4',
            long_name='Field 4',
            attr_type=models.AttributeType.objects.get(name='select_one'),
            choices=['one', 'two', 'three'],
            choice_labels=['Choice 1', 'Choice 2', 'Choice 3'],
            index=3,
        )

        party = factories.PartyFactory.create(
            project=project,
            attrs={'field_1': 'Some value',
                   'field_3': ['one', 'three'],
                   'field_4': 'two'}
        )

        view = JsonAttrsView()
        view.object = party
        context = view.get_context_data()
        assert len(context['attrs']) == 4

        assert context['attrs'][0] == ('Field 1', 'Some value', '', '')
        assert context['attrs'][1] == ('Field 2', '—', '', '')
        assert context['attrs'][2] == ('Field 3', 'Choice 1, Choice 3', '', '')
        assert context['attrs'][3] == ('Field 4', 'Choice 2', '', '')

    def test_get_context_xlang(self):
        models.create_attribute_types()
        org = factories.OrganizationFactory.create()
        project = factories.ProjectFactory.create(organization=org)
        content_type = ContentType.objects.get(
            app_label='tests', model='party')

        schema1 = models.Schema.objects.create(
            content_type=content_type,
            selectors=(org.id, project.id),
            default_language='en')

        models.Attribute.objects.create(
            schema=schema1,
            name='field_1',
            long_name={'en': 'Field 1', 'de': 'Feld 1'},
            attr_type=models.AttributeType.objects.get(name='text'),
            index=0
        )
        models.Attribute.objects.create(
            schema=schema1,
            name='field_2',
            long_name={'en': 'Field 2', 'de': 'Feld 2'},
            attr_type=models.AttributeType.objects.get(name='text'),
            index=1
        )
        models.Attribute.objects.create(
            schema=schema1,
            name='field_3',
            long_name={'en': 'Field 3', 'de': 'Feld 3'},
            attr_type=models.AttributeType.objects.get(name='select_multiple'),
            choices=['one', 'two', 'three'],
            choice_labels=[{'en': 'Choice 1', 'de': 'Wahl 1'},
                           {'en': 'Choice 2', 'de': 'Wahl 2'},
                           {'en': 'Choice 3', 'de': 'Wahl 3'}],
            index=2,
        )
        models.Attribute.objects.create(
            schema=schema1,
            name='field_4',
            long_name={'en': 'Field 4', 'de': 'Feld 4'},
            attr_type=models.AttributeType.objects.get(name='select_one'),
            choices=['one', 'two', 'three'],
            choice_labels=[{'en': 'Choice 1', 'de': 'Wahl 1'},
                           {'en': 'Choice 2', 'de': 'Wahl 2'},
                           {'en': 'Choice 3', 'de': 'Wahl 3'}],
            index=3,
        )

        party = factories.PartyFactory.create(
            project=project,
            attrs={'field_1': 'Some value',
                   'field_3': ['one', 'three'],
                   'field_4': 'two'}
        )

        view = JsonAttrsView()
        view.object = party
        context = view.get_context_data()
        assert len(context['attrs']) == 4

        field_1 = context['attrs'][0]
        assert field_1[0] == 'Field 1'
        assert field_1[1] == 'Some value'
        assert 'data-label-en="Field 1"' in field_1[2]
        assert 'data-label-de="Feld 1"' in field_1[2]

        field_2 = context['attrs'][1]
        assert field_2[0] == 'Field 2'
        assert field_2[1] == '—'
        assert 'data-label-en="Field 2"' in field_2[2]
        assert 'data-label-de="Feld 2"' in field_2[2]

        field_3 = context['attrs'][2]
        assert field_3[0] == 'Field 3'
        assert field_3[1] == 'Choice 1, Choice 3'
        assert 'data-label-en="Field 3"' in field_3[2]
        assert 'data-label-de="Feld 3"' in field_3[2]
        assert 'data-label-en="Choice 1, Choice 3"' in field_3[3]
        assert 'data-label-de="Wahl 1, Wahl 3"' in field_3[3]

        field_4 = context['attrs'][3]
        assert field_4[0] == 'Field 4'
        assert field_4[1] == 'Choice 2'
        assert 'data-label-en="Field 4"' in field_4[2]
        assert 'data-label-de="Feld 4"' in field_4[2]
        assert 'data-label-en="Choice 2"' in field_4[3]
        assert 'data-label-de="Wahl 2"' in field_4[3]
