import django.views.generic as generic
import django.views.generic.edit as edit
from django.core.urlresolvers import reverse_lazy
from django.forms import ModelForm, ModelChoiceField

from .models import Organization, Project, Party, Parcel


# ----------------------------------------------------------------------
#
#  HOME PAGE
#

class IndexView(generic.TemplateView):
    template_name = 'exampleapp/index.html'


# ----------------------------------------------------------------------
#
#  ORGANIZATIONS
#

class OrganizationList(generic.ListView):
    model = Organization
    permission_required = 'organization.list'


class OrganizationCreate(edit.CreateView):
    model = Organization
    fields = ('name',)
    success_url = reverse_lazy('organization-list')
    permission_required = {'GET': None, 'POST': 'organization.create'}


class OrganizationDelete(edit.DeleteView):
    model = Organization
    success_url = reverse_lazy('organization-list')
    permission_required = 'organization.delete'


# ----------------------------------------------------------------------
#
#  PROJECTS
#

class ProjectList(generic.ListView):
    model = Project
    permission_required = 'project.list'


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
    permission_required = {'GET': None, 'POST': 'project.create'}


class ProjectDelete(edit.DeleteView):
    model = Project
    success_url = reverse_lazy('project-list')
    permission_required = 'project.delete'


# ----------------------------------------------------------------------
#
#  PARTIES
#

class PartyList(generic.ListView):
    model = Party
    permission_required = 'party.list'


class PartyDetail(generic.DetailView):
    model = Party
    permission_required = 'party.detail'


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
    permission_required = {'GET': None, 'POST': 'party.create'}


class PartyUpdate(edit.UpdateView):
    model = Party
    form_class = PartyForm
    template_name_suffix = '_update_form'
    permission_required = {'GET': None, 'POST': 'party.edit'}


class PartyDelete(edit.DeleteView):
    model = Party
    success_url = reverse_lazy('party-list')
    permission_required = {'GET': None, 'POST': 'party.delete'}


# ----------------------------------------------------------------------
#
#  PARCELS
#

class ParcelList(generic.ListView):
    model = Parcel
    permission_required = 'parcel.list'


class ParcelDetail(generic.DetailView):
    model = Parcel
    permission_required = 'parcel.detail'


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
    permission_required = {'GET': None, 'POST': 'parcel.create'}


class ParcelUpdate(edit.UpdateView):
    model = Parcel
    form_class = ParcelForm
    template_name_suffix = '_update_form'
    permission_required = {'GET': None, 'POST': 'parcel.edit'}


class ParcelDelete(edit.DeleteView):
    model = Parcel
    success_url = reverse_lazy('parcel-list')
    permission_required = {'GET': None, 'POST': 'parcel.delete'}
