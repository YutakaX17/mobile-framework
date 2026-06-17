from django.urls import path

from .views import active_package_manifest


urlpatterns = [
    path("manifest/", active_package_manifest, name="active-package-manifest"),
]
