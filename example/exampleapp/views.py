import django.views.generic as generic
import django.views.generic.edit as edit
from django.shortcuts import redirect
from django.core.urlresolvers import reverse_lazy
from django.forms import ModelForm, ModelChoiceField
from django.contrib.contenttypes.models import ContentType
import django.db.transaction as transaction

from jsonattrs.models import Schema, SchemaSelector

from .models import Organization, Project, Party, Parcel
from .forms import SchemaForm


org_t = ContentType.objects.get(app_label='exampleapp', model='organization')
proj_t = ContentType.objects.get(app_label='exampleapp', model='project')


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
            key += row['organization'].name if row['organization'] else ' '
            key += ':'
            key += row['project'].name if row['project'] else ' '
            return key

        context = super().get_context_data(*args, **kwargs)
        table_data = []
        for schema in context['object_list']:
            org_selector = schema.selectors.get(index=1)
            proj_selector = schema.selectors.get(index=2)
            table_data.append({'content_type': schema.content_type,
                               'organization': org_selector.selector,
                               'project': proj_selector.selector})
        context['table_data'] = sorted(table_data, key=row_key)
        return context


class SchemaCreate(generic.FormView):
    model = Schema
    form_class = SchemaForm
    template_name = 'jsonattrs/schema_form.html'
    success_url = reverse_lazy('schema-list')

    def post(self, request):
        content_type = ContentType.objects.get(pk=request.POST['content_type'])
        org = None
        if request.POST['organization']:
            org = Organization.objects.get(pk=request.POST['organization'])
        project = None
        if request.POST['project']:
            project = Project.objects.get(pk=request.POST['project'])
        with transaction.atomic():
            schema = Schema.objects.create(content_type=content_type)
            SchemaSelector.objects.create(
                schema=schema, index=1, content_type=org_t,
                object_id=org.pk if org else None
            )
            SchemaSelector.objects.create(
                schema=schema, index=2, content_type=proj_t,
                object_id=project.pk if project else None
            )
        return redirect(self.success_url)


# ----------------------------------------------------------------------
#
#  ORGANIZATIONS
#

class OrganizationList(generic.ListView):
    model = Organization


class OrganizationCreate(edit.CreateView):
    model = Organization
    fields = ('name',)
    success_url = reverse_lazy('organization-list')


class OrganizationDelete(edit.DeleteView):
    model = Organization
    success_url = reverse_lazy('organization-list')


# ----------------------------------------------------------------------
#
#  PROJECTS
#

class ProjectList(generic.ListView):
    model = Project


class ProjectForm(ModelForm):
    class Meta:
        model = Project
        fields = ('name', 'organization')

    def __init__(self, *args, **kwargs):
        super(ProjectForm, self).__init__(*args, **kwargs)
        self.fields['organization'] = ModelChoiceField(
            queryset=Organization.objects.all(), empty_label=None
        )


class ProjectCreate(edit.CreateView):
    model = Project
    form_class = ProjectForm
    success_url = reverse_lazy('project-list')


class ProjectDelete(edit.DeleteView):
    model = Project
    success_url = reverse_lazy('project-list')


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
        fields = ('name', 'project')

    def __init__(self, *args, **kwargs):
        super(PartyForm, self).__init__(*args, **kwargs)
        self.fields['project'] = ModelChoiceField(
            queryset=Project.objects.all(), empty_label=None
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
#  PARCELS
#

class ParcelList(generic.ListView):
    model = Parcel


class ParcelDetail(generic.DetailView):
    model = Parcel


class ParcelForm(ModelForm):
    class Meta:
        model = Parcel
        fields = ('address', 'project')

    def __init__(self, *args, **kwargs):
        super(ParcelForm, self).__init__(*args, **kwargs)
        self.fields['project'] = ModelChoiceField(
            queryset=Project.objects.all(), empty_label=None
        )


class ParcelCreate(edit.CreateView):
    model = Parcel
    form_class = ParcelForm


class ParcelUpdate(edit.UpdateView):
    model = Parcel
    form_class = ParcelForm
    template_name_suffix = '_update_form'


class ParcelDelete(edit.DeleteView):
    model = Parcel
    success_url = reverse_lazy('parcel-list')
