from django.urls import path

from .views import module_detail, module_list


urlpatterns = [
    path("", module_list, name="module-list"),
    path("<slug:module_id>/", module_detail, name="module-detail"),
]
