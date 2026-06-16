from django.urls import path

from .views import form_detail, form_list


urlpatterns = [
    path("", form_list, name="form-list"),
    path("<slug:form_id>/", form_detail, name="form-detail"),
]
