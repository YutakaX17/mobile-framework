from django.urls import path

from .views import active_package_manifest, package_download


urlpatterns = [
    path("manifest/", active_package_manifest, name="active-package-manifest"),
    path("<slug:package_id>/download/", package_download, name="package-download"),
]
