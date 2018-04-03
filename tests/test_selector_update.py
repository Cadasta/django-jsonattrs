import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError

from jsonattrs.exceptions import SchemaUpdateConflict, SchemaUpdateException

from .fixtures import create_fixtures, create_labelled_schemata
from .models import Party, Labelled


class SchemaUpdateExceptionTest(TestCase):
    def test_exception_str(self):
        exc = SchemaUpdateException(conflicts=[
                SchemaUpdateConflict('field1', 'incompatible_type'),
                SchemaUpdateConflict('field2', 'required_no_default')
        ])
        assert str(exc) == ("SchemaUpdateException: "
                            "[\"Incompatible change in type of field "
                            "'field1'\", \"Required field 'field2' added "
                            "without supplying a default value\"]")
        assert repr(exc) == ("SchemaUpdateException: "
                             "[\"Incompatible change in type of field "
                             "'field1'\", \"Required field 'field2' added "
                             "without supplying a default value\"]")

    def test_conflict_type_checking(self):
        conf1 = SchemaUpdateConflict('field1', 'required_no_default')
        assert conf1.message() == ("Required field 'field1' added "
                                   "without supplying a default value")
        with pytest.raises(ValueError):
            conf2 = SchemaUpdateConflict('field2', 'xyz')
            assert conf2

    def test_exception_messages(self):
        with pytest.raises(SchemaUpdateException) as exc_info:
            raise SchemaUpdateException(conflicts=[
                SchemaUpdateConflict('field1', 'incompatible_type'),
                SchemaUpdateConflict('field2', 'required_no_default')
            ])
        assert (exc_info.value.messages ==
                ["Incompatible change in type of field 'field1'",
                 "Required field 'field2' added without "
                 "supplying a default value"])


class SelectorUpdateTest(TestCase):
    def setUp(self):
        self.fixtures, self.schemata = create_fixtures()

    def test_selector_update_schema(self):
        tstparty = Party.objects.create(
            project=self.fixtures['proj11'],
            name='Bilbo Baggins', attrs={'dob': '1972-05-10'}
        )
        assert 'dob' in tstparty.attrs.attributes
        assert 'gender' in tstparty.attrs.attributes
        assert 'education' in tstparty.attrs.attributes
        assert 'homeowner' in tstparty.attrs.attributes
        assert len(tstparty.attrs.attributes) == 4

        tstparty.project = self.fixtures['proj12']
        tstparty.save()
        assert 'dob' not in tstparty.attrs.attributes
        assert 'gender' in tstparty.attrs.attributes
        assert 'education' in tstparty.attrs.attributes
        assert 'homeowner' in tstparty.attrs.attributes
        assert len(tstparty.attrs.attributes) == 3


class LabelledModelTest(TestCase):
    def setUp(self):
        create_labelled_schemata()

    def check(self, present, absent=None):
        for f in present:
            assert f in self.obj.attrs.attributes
        assert len(self.obj.attrs.attributes) == len(present)
        if absent is not None:
            for f in absent:
                assert f not in self.obj.attrs.attributes


class BasicLabelledModelTest(LabelledModelTest):
    def test_ok(self):
        self.obj = Labelled.objects.create(
            name='initial',
            label='initial',
            attrs={'f1': 'ABC', 'f2': 'f2_val', 'f3': 123, 'f4': 'def'}
        )
        self.check(('f1', 'f2', 'f3', 'f4'))

    def test_bad_1(self):
        with pytest.raises(ValidationError) as exc_info:
            self.obj = Labelled.objects.create(
                name='initial',
                label='initial',
                attrs={'f1': 'ABC', 'f2': 'f2_val', 'f3': 'abc', 'f4': 'def'}
            )
            self.check(('f1', 'f2', 'f3', 'f4'))
        assert exc_info.value.messages == ['Validation failed for f3: "abc"']

    def test_bad_2(self):
        with pytest.raises(ValidationError) as exc_info:
            self.obj = Labelled.objects.create(
                name='initial',
                label='initial',
                attrs={'f1': 'ABC', 'f2': 'f2_val', 'f3': 123, 'f4': 'XYZ'}
            )
            self.check(('f1', 'f2', 'f3', 'f4'))
        assert exc_info.value.messages == ['Invalid choice for f4: "XYZ"']


class LabelledSelectorUpdateTest(LabelledModelTest):
    def setUp(self):
        super().setUp()
        self.obj = Labelled.objects.create(
            name='initial',
            label='initial',
            attrs={'f1': 'ABC', 'f2': 'f2_val', 'f3': 123, 'f4': 'def'}
        )
        self.check(('f1', 'f2', 'f3', 'f4'))

    def doit(self, label, present, absent=None):
        self.obj.label = label
        self.obj.save()
        self.check(present, absent=absent)

    def test_remove_non_required_field(self):
        self.doit('remove_non_required',
                  present=('f2', 'f3', 'f4'), absent=('f1',))

    def test_remove_required_field(self):
        self.doit('remove_required',
                  present=('f1', 'f3', 'f4'), absent=('f2',))

    def test_add_new_non_required_field(self):
        self.doit('new_non_required',
                  present=('f1', 'f2', 'f3', 'f4', 'f5'))

    def test_add_new_required_field_no_default(self):
        with pytest.raises(SchemaUpdateException) as exc_info:
            self.doit('new_required_no_default',
                      present=('f1', 'f2', 'f3', 'f4', 'f5'))
        assert exc_info.value.messages == [
            "Required field 'f5' added without supplying a default value"
        ]

    def test_add_new_required_field_default(self):
        self.doit('new_required_default',
                  present=('f1', 'f2', 'f3', 'f4', 'f5'))
        assert self.obj.attrs['f5'] == 'default'

    def test_change_field_type_compatible(self):
        self.doit('type_compatible',
                  present=('f1', 'f2', 'f3', 'f4'))

    def test_change_field_type_incompatible(self):
        with pytest.raises(SchemaUpdateException) as exc_info:
            self.doit('type_incompatible',
                      present=('f1', 'f2', 'f3', 'f4'))
        assert exc_info.value.messages == [
            "Incompatible change in type of field 'f2'"
        ]

    def test_remove_choices_list(self):
        self.doit('remove_choices',
                  present=('f1', 'f2', 'f3', 'f4'))

    def test_add_choices_list_include_current(self):
        self.doit('add_choices',
                  present=('f1', 'f2', 'f3', 'f4'))

    def test_add_choices_list_exclude_current(self):
        self.obj.attrs['f1'] = 'XYZ'
        self.doit('add_choices',
                  present=('f1', 'f2', 'f3', 'f4'))

    def test_change_choices_list_include_current(self):
        self.obj.attrs['f4'] = 'ghi'
        self.doit('change_choices',
                  present=('f1', 'f2', 'f3', 'f4'))

    def test_change_choices_list_exclude_current(self):
        self.doit('change_choices',
                  present=('f1', 'f2', 'f3', 'f4'))
