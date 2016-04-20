from django.contrib import admin

from .models import Organization, Project, Party, Parcel

admin.site.register(Organization)
admin.site.register(Project)
admin.site.register(Party)
admin.site.register(Parcel)
