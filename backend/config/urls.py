"""Root URL configuration for the backend control plane."""

from django.urls import include, path


urlpatterns = [
    path("health/", include("apps.core.urls")),
]
