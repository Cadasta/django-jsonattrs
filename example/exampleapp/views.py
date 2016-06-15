import django.views.generic as generic
import django.views.generic.edit as edit
from django.shortcuts import redirect
from django.core.urlresolvers import reverse_lazy
from django.forms import ModelChoiceField
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError
import django.db.transaction as transaction
from django.db.utils import OperationalError, ProgrammingError

from jsonattrs.models import Schema
from jsonattrs.forms import AttributeModelForm

from .models import Division, Department, Party, Contract
from .forms import SchemaForm, AttributeFormSet, PartyForm


try:
    div_t = ContentType.objects.get(app_label='exampleapp',
                                    model='division')
    dept_t = ContentType.objects.get(app_label='exampleapp',
                                     model='department')
# These can happen when constructing database migrations from scratch.
except OperationalError:
    pass
except ProgrammingError:
    pass


# ----------------------------------------------------------------------
#
#  HOME PAGE
#

class IndexView(generic.TemplateView):
    template_name = 'exampleapp/index.html'


# ----------------------------------------------------------------------
#
#  SCHEMATA
#

class SchemaList(generic.ListView):
    model = Schema

    def get_context_data(self, *args, **kwargs):
        def row_key(row):
            key = str(row['content_type'])
            key += ':'
            key += row['division'] if row['division'] else ' '
            key += ':'
            key += row['department'] if row['department'] else ' '
            return key

        context = super().get_context_data(*args, **kwargs)
        table_data = []
        for schema in context['object_list']:
            sel = schema.selectors
            nsel = len(sel)
            div_selector = (Division.objects.get(pk=sel[0]).name
                            if nsel > 0 else None)
            dept_selector = (Department.objects.get(pk=sel[1]).name
                             if nsel > 1 else None)
            table_data.append({'content_type': schema.content_type,
                               'division': div_selector,
                               'department': dept_selector,
                               'schema': schema})
        context['table_data'] = sorted(table_data, key=row_key)
        return context


class SchemaMixin:
    form_class = SchemaForm
    success_url = reverse_lazy('schema-list')

    def get_initial(self):
        obj = self.get_object()
        if obj is not None:
            sels = obj.selectors
            return {'content_type': obj.content_type,
                    'division': (Division.objects.get(pk=sels[0])
                                 if len(sels) > 0 else None),
                    'department': (Department.objects.get(pk=sels[1])
                                   if len(sels) > 1 else None)}
        else:
            return {}

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        obj = self.get_object()
        if obj is not None:
            kwargs.update({'instance': obj})
        return kwargs

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if not hasattr(self, 'formset'):
            if self.get_object() is not None:
                self.formset = AttributeFormSet(instance=self.get_object())
            else:
                self.formset = AttributeFormSet()
        context['formset'] = self.formset
        context['empty_row'] = self.formset.empty_form
        return context

    def form_valid(self, form):
        content_type = ContentType.objects.get(
            pk=self.request.POST['content_type']
        )
        selectors = ()
        div = None
        dept = None
        if self.request.POST['division']:
            div = self.request.POST['division']
            selectors = (div,)
            if self.request.POST['department']:
                dept = self.request.POST['department']
                selectors = (div, dept)
        try:
            with transaction.atomic():
                self.set_up_schema(content_type, selectors)
                self.formset = AttributeFormSet(
                    self.request.POST, self.request.FILES,
                    instance=self.schema
                )
                if not self.formset.is_valid():
                    raise IntegrityError
                self.formset.save()
        except:
            return self.form_invalid(self.get_form())
        else:
            return redirect(self.success_url)


class SchemaCreate(SchemaMixin, generic.FormView):
    template_name = 'jsonattrs/schema_create_form.html'

    def get_object(self):
        return self.schema if hasattr(self, 'schema') else None

    def set_up_schema(self, content_type, selectors):
        self.schema = Schema.objects.create(
            content_type=content_type,
            selectors=selectors
        )


class SchemaUpdate(SchemaMixin, generic.FormView):
    template_name = 'jsonattrs/schema_update_form.html'

    def get_object(self):
        return (self.schema if hasattr(self, 'schema')
                else Schema.objects.get(pk=self.kwargs['pk']))

    def set_up_schema(self, content_type, selectors):
        self.schema = Schema.objects.get(
            content_type=content_type,
            selectors=selectors
        )


class SchemaDelete(edit.DeleteView):
    model = Schema
    success_url = reverse_lazy('schema-list')


# ----------------------------------------------------------------------
#
#  ENTITY ATTRIBUTES
#

class EntityAttributesMixin:
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['attrs'] = context['object'].attrs.attributes.values()
        return context

    def form_valid(self, form):
        print('EntityAttributesMixin.form_valid:', self.request.POST)
        return super().form_valid(form)

    def form_invalid(self, form):
        print('EntityAttributesMixin.form_invalid:', self.request.POST)
        return super().form_invalid(form)


# ----------------------------------------------------------------------
#
#  DIVISION/DEPARTMENT MENU
#

class DivisionDepartmentMixin:
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        divdepts = []
        for div in Division.objects.all():
            for dept in div.departments.all():
                divdepts.append((div.name + '/' + dept.name,
                                 (div.pk, dept.pk)))
        context['divdepts'] = divdepts
        return context


# ----------------------------------------------------------------------
#
#  DIVISIONS
#

class DivisionList(generic.ListView):
    model = Division


class DivisionDetail(EntityAttributesMixin, generic.DetailView):
    model = Division


class DivisionCreate(edit.CreateView):
    model = Division
    fields = ('name',)
    success_url = reverse_lazy('division-list')


class DivisionDelete(edit.DeleteView):
    model = Division
    success_url = reverse_lazy('division-list')


# ----------------------------------------------------------------------
#
#  DEPARTMENTS
#

class DepartmentList(generic.ListView):
    model = Department


class DepartmentDetail(EntityAttributesMixin, generic.DetailView):
    model = Department


class DepartmentForm(AttributeModelForm):
    class Meta:
        model = Department
        fields = ('name', 'division')

    def __init__(self, *args, **kwargs):
        super(DepartmentForm, self).__init__(*args, **kwargs)
        self.fields['division'] = ModelChoiceField(
            queryset=Division.objects.all(), empty_label=None
        )


class DepartmentCreate(edit.CreateView):
    model = Department
    form_class = DepartmentForm
    success_url = reverse_lazy('department-list')


class DepartmentDelete(edit.DeleteView):
    model = Department
    success_url = reverse_lazy('department-list')


# ----------------------------------------------------------------------
#
#  PARTIES
#

class PartyList(generic.ListView):
    model = Party


class PartyDetail(EntityAttributesMixin, generic.DetailView):
    model = Party


class PartyCreate(edit.CreateView):
    model = Party
    form_class = PartyForm


class PartyUpdate(EntityAttributesMixin, edit.UpdateView):
    model = Party
    form_class = PartyForm
    template_name_suffix = '_update_form'


class PartyDelete(edit.DeleteView):
    model = Party
    success_url = reverse_lazy('party-list')


# ----------------------------------------------------------------------
#
#  CONTRACTS
#

class ContractList(generic.ListView):
    model = Contract


class ContractDetail(EntityAttributesMixin, generic.DetailView):
    model = Contract


class ContractForm(AttributeModelForm):
    class Meta:
        model = Contract
        fields = ('department',)

    def __init__(self, *args, **kwargs):
        super(ContractForm, self).__init__(*args, **kwargs)
        self.fields['department'] = ModelChoiceField(
            queryset=Department.objects.all(), empty_label=None
        )


class ContractCreate(edit.CreateView):
    model = Contract
    form_class = ContractForm


class ContractUpdate(edit.UpdateView):
    model = Contract
    form_class = ContractForm
    template_name_suffix = '_update_form'


class ContractDelete(edit.DeleteView):
    model = Contract
    success_url = reverse_lazy('contract-list')
