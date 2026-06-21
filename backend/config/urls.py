"""Root URL configuration for the backend control plane."""

from django.urls import include, path


urlpatterns = [
    path("api/apps/", include("apps.app_builder.urls")),
    path("api/auth/", include("apps.identity.urls")),
    path("api/deployment-packages/", include("apps.deployment_packages.admin_urls")),
    path("api/forms/", include("apps.form_builder.urls")),
    path("api/mobile/packages/", include("apps.deployment_packages.urls")),
    path("api/modules/", include("apps.modules.urls")),
    path("api/themes/", include("apps.themes.urls")),
    path("health/", include("apps.core.urls")),
]
