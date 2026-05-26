from django.contrib import admin
from .models import *


admin.site.register(Company)
admin.site.register(DataSource)
admin.site.register(RawRecord)
admin.site.register(EmissionFactor)
admin.site.register(PlantCodeLookup)
admin.site.register(NormalizedEmissionRecord)
admin.site.register(AuditLog)