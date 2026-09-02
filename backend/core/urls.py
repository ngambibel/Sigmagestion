"""Routes du noyau."""
from django.urls import path

from .views import SanteView

urlpatterns = [
    path("sante/", SanteView.as_view(), name="sante"),
]
