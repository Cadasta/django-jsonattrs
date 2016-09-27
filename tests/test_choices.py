import pytest
from django.test import TestCase

from jsonattrs.models import Schema, Attribute, AttributeType

from .fixtures import create_fixtures


class ChoicesTest(TestCase):
    def setUp(self):
        self.fixtures = create_fixtures(do_schemas=False, load_attr_types=True)
        self.schema = Schema.objects.create(
            content_type=self.fixtures['party_t'], selectors=()
        )

    def create_attr(self, choices=None, choice_labels=None):
        return Attribute.objects.create(
            schema=self.schema,
            name='testattr',
            long_name='Test attribute',
            index=1,
            attr_type=AttributeType.objects.get(name='select_one'),
            choices=choices,
            choice_labels=choice_labels
        )

    def test_choices_no_choice_labels(self):
        attr = self.create_attr(
            choices=['a', 'b', 'c']
        )
        assert attr.choice_dict['a'] == 'a'

    def test_choices_with_choice_labels(self):
        attr = self.create_attr(
            choices=['a', 'b', 'c'],
            choice_labels=['Choice A', 'Choice B', 'Choice C']
        )
        assert attr.choice_dict['a'] == 'Choice A'

    def test_tuple_choices(self):
        attr = self.create_attr(
            choices=[('a', 'Choice A'), ('b', 'Choice B'), ('c', 'Choice C')]
        )
        assert attr.choice_dict['a'] == 'Choice A'

    def test_bad_tuple_choices(self):
        with pytest.raises(ValueError):
            self.create_attr(choices=[('a', 'Choice A'), 'b'])

    def test_no_choices_but_choice_labels(self):
        with pytest.raises(ValueError):
            self.create_attr(choice_labels=['Choice A', 'Choice B'])

    def test_choices_choice_labels_len_mismatch(self):
        with pytest.raises(ValueError):
            self.create_attr(choices=('a', 'b', 'c'),
                             choice_labels=["Choice A", "Choice B"])
