from django.urls import path

from .views import theme_detail, theme_list


urlpatterns = [
    path("", theme_list, name="theme-list"),
    path("<slug:theme_id>/", theme_detail, name="theme-detail"),
]
