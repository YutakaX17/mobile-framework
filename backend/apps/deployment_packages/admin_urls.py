from django.urls import path

from .views import admin_package_activate, admin_package_compile, admin_package_detail, admin_package_list


urlpatterns = [
    path("", admin_package_list, name="admin-package-list"),
    path("compile/", admin_package_compile, name="admin-package-compile"),
    path("<slug:package_id>/", admin_package_detail, name="admin-package-detail"),
    path("<slug:package_id>/activate/", admin_package_activate, name="admin-package-activate"),
]
