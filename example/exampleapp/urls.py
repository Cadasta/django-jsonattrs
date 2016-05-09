from django.conf.urls import url

from .views import (
    IndexView,
    SchemaList, SchemaCreate, SchemaUpdate, SchemaDelete,
    DivisionList, DivisionCreate, DivisionDelete,
    DepartmentList, DepartmentCreate, DepartmentDelete,
    PartyList, PartyDetail, PartyCreate, PartyUpdate, PartyDelete,
    ContractList, ContractDetail, ContractCreate, ContractUpdate,
    ContractDelete)

urlpatterns = [
    url(r'^$', IndexView.as_view(), name='index'),

    url(r'^schema/$', SchemaList.as_view(),
        name='schema-list'),
    url(r'^schema/(?P<pk>\d+)/$', SchemaUpdate.as_view(),
        name='schema-detail'),
    url(r'^schema/add/$', SchemaCreate.as_view(),
        name='schema-add'),
    url(r'^schema/(?P<pk>\d+)/delete/$', SchemaDelete.as_view(),
        name='schema-delete'),

    url(r'^division/$', DivisionList.as_view(),
        name='division-list'),
    url(r'^division/add/$', DivisionCreate.as_view(),
        name='division-add'),
    url(r'^division/(?P<pk>\d+)/delete/$', DivisionDelete.as_view(),
        name='division-delete'),

    url(r'^department/$', DepartmentList.as_view(), name='department-list'),
    url(r'^department/add/$', DepartmentCreate.as_view(),
        name='department-add'),
    url(r'^department/(?P<pk>\d+)/delete/$', DepartmentDelete.as_view(),
        name='department-delete'),

    url(r'^party/$', PartyList.as_view(), name='party-list'),
    url(r'^party/(?P<pk>\d+)/$', PartyDetail.as_view(), name='party-detail'),
    url(r'^party/add/$', PartyCreate.as_view(), name='party-add'),
    url(r'^party/(?P<pk>\d+)/edit/$', PartyUpdate.as_view(),
        name='party-update'),
    url(r'^party/(?P<pk>\d+)/delete/$', PartyDelete.as_view(),
        name='party-delete'),

    url(r'^contract/$', ContractList.as_view(), name='contract-list'),
    url(r'^contract/(?P<pk>\d+)/$', ContractDetail.as_view(),
        name='contract-detail'),
    url(r'^contract/add/$', ContractCreate.as_view(), name='contract-add'),
    url(r'^contract/(?P<pk>\d+)/edit/$', ContractUpdate.as_view(),
        name='contract-update'),
    url(r'^contract/(?P<pk>\d+)/delete/$', ContractDelete.as_view(),
        name='contract-delete'),
]
