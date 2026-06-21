from django.urls import path

from .views import form_detail, form_list, form_revision_publish, form_submit


urlpatterns = [
    path("", form_list, name="form-list"),
    path("<slug:form_id>/revisions/<int:revision>/publish/", form_revision_publish, name="form-revision-publish"),
    path("<slug:form_id>/submissions/", form_submit, name="form-submit"),
    path("<slug:form_id>/", form_detail, name="form-detail"),
]
