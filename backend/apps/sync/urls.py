from django.urls import path

from .views import register_device, submit_outbox, sync_status


urlpatterns = [
    path("devices/", register_device, name="sync-register-device"),
    path("outbox/", submit_outbox, name="sync-submit-outbox"),
    path("status/", sync_status, name="sync-status"),
]
