from django.urls import path
from .views import health_check, get_records
from .views import upload_sap_csv, upload_utility_csv, upload_travel_csv
from .views import approve_record, reject_record

urlpatterns = [
    path("health/", health_check),
    path("records/", get_records),
    path("upload/sap/", upload_sap_csv),
    path("upload/utility/", upload_utility_csv),
    path("upload/travel/", upload_travel_csv),
    path("records/<int:record_id>/approve/", approve_record),
    path("records/<int:record_id>/reject/", reject_record),
    
]