"""Routes des rapports et du tableau de bord."""
from django.urls import path

from .views import TableauDeBordEmployeView, TableauDeBordView

urlpatterns = [
    path("tableau-de-bord/", TableauDeBordView.as_view(), name="tableau-de-bord"),
    path(
        "tableau-de-bord/employe/",
        TableauDeBordEmployeView.as_view(), name="tableau-de-bord-employe",
    ),
]
