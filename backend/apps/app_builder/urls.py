from django.urls import path

from .views import app_detail, app_list


urlpatterns = [
    path("", app_list, name="app-list"),
    path("<slug:app_id>/", app_detail, name="app-detail"),
]
