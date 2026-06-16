from django.urls import path

from .views import theme_detail, theme_list, theme_revision_publish, theme_revision_rollback


urlpatterns = [
    path("", theme_list, name="theme-list"),
    path("<slug:theme_id>/revisions/<int:revision>/publish/", theme_revision_publish, name="theme-revision-publish"),
    path("<slug:theme_id>/revisions/<int:revision>/rollback/", theme_revision_rollback, name="theme-revision-rollback"),
    path("<slug:theme_id>/", theme_detail, name="theme-detail"),
]
