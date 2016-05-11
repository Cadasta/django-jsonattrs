import django.views.generic as generic
import django.views.generic.edit as edit
from django.shortcuts import redirect
from django.core.urlresolvers import reverse_lazy
from django.forms import ModelForm, ModelChoiceField
from django.contrib.contenttypes.models import ContentType
import django.db.transaction as transaction
from django.db.utils import OperationalError

from jsonattrs.models import Schema

from .models import Division, Department, Party, Contract
from .forms import SchemaForm, AttributeFormSet


try:
    div_t = ContentType.objects.get(app_label='exampleapp',
                                    model='division')
    dept_t = ContentType.objects.get(app_label='exampleapp',
                                     model='department')
except OperationalError:
    # Happens when constructing database migrations from scratch.
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
            div_selector = None
            if schema.selectors.count() > 0:
                div_selector = schema.selectors.get(index=1).selector.name
            dept_selector = None
            if schema.selectors.count() > 1:
                dept_selector = schema.selectors.get(index=2).selector.name
            table_data.append({'content_type': schema.content_type,
                               'division': div_selector,
                               'department': dept_selector,
                               'schema': schema})
        context['table_data'] = sorted(table_data, key=row_key)
        return context


class SchemaMixin:
    form_class = SchemaForm

    def get_initial(self):
        obj = self.get_object()
        if obj is not None:
            sels = obj.selectors.all()
            return {'content_type': obj.content_type,
                    'division': sels[0].selector if len(sels) > 0 else None,
                    'department': sels[1].selector if len(sels) > 1 else None}
        else:
            return {}

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
            div = Division.objects.get(
                pk=self.request.POST['division']
            )
            selectors = (div,)
            if self.request.POST['department']:
                dept = Department.objects.get(
                    pk=self.request.POST['department']
                )
                selectors = (div, dept)
        try:
            self.process(self.request, content_type, selectors)
        except:
            return self.form_invalid(self.get_form())
        else:
            return redirect(self.success_url)


class SchemaCreate(SchemaMixin, generic.FormView):
    template_name = 'jsonattrs/schema_create_form.html'
    success_url = reverse_lazy('schema-list')

    def get_object(self):
        return self.schema if hasattr(self, 'schema') else None

    def process(self, request, content_type, selectors):
        with transaction.atomic():
            self.schema = Schema.objects.create(
                content_type=content_type, selectors=selectors
            )
            print('SchemaCreate.process:', request.POST)
            self.formset = AttributeFormSet(
                request.POST, request.FILES, instance=self.schema
            )
            if not self.formset.is_valid():
                print('Formset is bad:', self.formset.errors)
                print(self.formset.data)
                raise transaction.IntegrityError
            self.formset.save()


class SchemaUpdate(SchemaMixin, generic.FormView):
    template_name = 'jsonattrs/schema_update_form.html'
    success_url = reverse_lazy('schema-list')

    def get_object(self):
        print('SchemaUpdate: get_object')
        return Schema.objects.get(pk=self.kwargs['pk'])

    def process(self, request, content_type, selectors):
        with transaction.atomic():
            schema = self.instance  # ???
            schema.content_type = content_type
            schema.selectors = selectors
            schema.save()
            formset = AttributeFormSet(request.POST, request.FILES)
            if not formset.is_valid():
                print('Formset is bad')
                print(formset)
                raise transaction.IntegrityError
            formset.save()


class SchemaDelete(edit.DeleteView):
    model = Schema
    success_url = reverse_lazy('schema-list')


# ----------------------------------------------------------------------
#
#  DIVISIONS
#

class DivisionList(generic.ListView):
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


class DepartmentForm(ModelForm):
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


class PartyDetail(generic.DetailView):
    model = Party


class PartyForm(ModelForm):
    class Meta:
        model = Party
        fields = ('name', 'department')

    def __init__(self, *args, **kwargs):
        super(PartyForm, self).__init__(*args, **kwargs)
        self.fields['department'] = ModelChoiceField(
            queryset=Department.objects.all(), empty_label=None
        )


class PartyCreate(edit.CreateView):
    model = Party
    form_class = PartyForm


class PartyUpdate(edit.UpdateView):
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


class ContractDetail(generic.DetailView):
    model = Contract


class ContractForm(ModelForm):
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
