import django.views.generic as generic
import django.views.generic.edit as edit
from django.shortcuts import redirect
from django.core.urlresolvers import reverse_lazy
from django.forms import ModelForm, ModelChoiceField
from django.contrib.contenttypes.models import ContentType
import django.db.transaction as transaction
from django.db.utils import OperationalError

from jsonattrs.models import Schema, SchemaSelector

from .models import Division, Department, Party, Contract
from .forms import SchemaForm


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
            key += row['division'].name if row['division'] else ' '
            key += ':'
            key += row['department'].name if row['department'] else ' '
            return key

        context = super().get_context_data(*args, **kwargs)
        table_data = []
        for schema in context['object_list']:
            div_selector = schema.selectors.get(index=1)
            dept_selector = schema.selectors.get(index=2)
            table_data.append({'content_type': schema.content_type,
                               'division': div_selector.selector,
                               'department': dept_selector.selector,
                               'schema': schema})
        context['table_data'] = sorted(table_data, key=row_key)
        return context


class SchemaCreate(generic.FormView):
    model = Schema
    form_class = SchemaForm
    template_name = 'jsonattrs/schema_form.html'
    success_url = reverse_lazy('schema-list')

    def post(self, request):
        content_type = ContentType.objects.get(pk=request.POST['content_type'])
        div = None
        if request.POST['division']:
            div = Division.objects.get(pk=request.POST['division'])
        dept = None
        if request.POST['department']:
            dept = Department.objects.get(pk=request.POST['department'])
        with transaction.atomic():
            schema = Schema.objects.create(content_type=content_type)
            SchemaSelector.objects.create(
                schema=schema, index=1, content_type=div_t,
                object_id=div.pk if div else None
            )
            SchemaSelector.objects.create(
                schema=schema, index=2, content_type=dept_t,
                object_id=dept.pk if dept else None
            )
        return redirect(self.success_url)


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
