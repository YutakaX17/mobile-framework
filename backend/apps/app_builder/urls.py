from django.urls import path

from .views import app_detail, app_list, app_revision_publish


urlpatterns = [
    path("", app_list, name="app-list"),
    path("<slug:app_id>/", app_detail, name="app-detail"),
    path("<slug:app_id>/revisions/<int:revision>/publish/", app_revision_publish, name="app-revision-publish"),
]
