from django.urls import path

from .views import csrf_token, current_session, current_tenant, login_view, logout_view, tenant_list


urlpatterns = [
    path("csrf/", csrf_token, name="identity-csrf"),
    path("login/", login_view, name="identity-login"),
    path("logout/", logout_view, name="identity-logout"),
    path("session/", current_session, name="identity-session"),
    path("tenants/", tenant_list, name="identity-tenant-list"),
    path("tenant/", current_tenant, name="identity-current-tenant"),
]
