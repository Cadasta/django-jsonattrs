from django.conf.urls import url

from .views import (
    IndexView,
    OrganizationList, OrganizationCreate, OrganizationDelete,
    ProjectList, ProjectCreate, ProjectDelete,
    PartyList, PartyDetail, PartyCreate, PartyUpdate, PartyDelete,
    ParcelList, ParcelDetail, ParcelCreate, ParcelUpdate, ParcelDelete)

urlpatterns = [
    url(r'^$', IndexView.as_view(), name='index'),

    url(r'^organization/$', OrganizationList.as_view(),
        name='organization-list'),
    url(r'^organization/add/$', OrganizationCreate.as_view(),
        name='organization-add'),
    url(r'^organization/(?P<pk>\d+)/delete/$', OrganizationDelete.as_view(),
        name='organization-delete'),

    url(r'^project/$', ProjectList.as_view(), name='project-list'),
    url(r'^project/add/$', ProjectCreate.as_view(), name='project-add'),
    url(r'^project/(?P<pk>\d+)/delete/$', ProjectDelete.as_view(),
        name='project-delete'),

    url(r'^party/$', PartyList.as_view(), name='party-list'),
    url(r'^party/(?P<pk>\d+)/$', PartyDetail.as_view(), name='party-detail'),
    url(r'^party/add/$', PartyCreate.as_view(), name='party-add'),
    url(r'^party/(?P<pk>\d+)/edit/$', PartyUpdate.as_view(),
        name='party-update'),
    url(r'^party/(?P<pk>\d+)/delete/$', PartyDelete.as_view(),
        name='party-delete'),

    url(r'^parcel/$', ParcelList.as_view(), name='parcel-list'),
    url(r'^parcel/(?P<pk>\d+)/$', ParcelDetail.as_view(),
        name='parcel-detail'),
    url(r'^parcel/add/$', ParcelCreate.as_view(), name='parcel-add'),
    url(r'^parcel/(?P<pk>\d+)/edit/$', ParcelUpdate.as_view(),
        name='parcel-update'),
    url(r'^parcel/(?P<pk>\d+)/delete/$', ParcelDelete.as_view(),
        name='parcel-delete'),
]
