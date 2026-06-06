from django.contrib.admin import site
from django.urls import path
from django.views.generic.base import RedirectView

urlpatterns = [
    path("", RedirectView.as_view(url="/admin/", permanent=False)),
    path("admin/", site.urls),
]
