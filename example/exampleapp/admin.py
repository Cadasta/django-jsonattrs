from django.contrib import admin

from .models import Division, Department, Party, Contract

admin.site.register(Division)
admin.site.register(Department)
admin.site.register(Party)
admin.site.register(Contract)
