"""Routes d'authentification et de profil."""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import ConnexionView, DeconnexionView, InscriptionView, MoiView

urlpatterns = [
    path("auth/inscription/", InscriptionView.as_view(), name="inscription"),
    path("auth/connexion/", ConnexionView.as_view(), name="connexion"),
    path("auth/rafraichir/", TokenRefreshView.as_view(), name="rafraichir"),
    path("auth/deconnexion/", DeconnexionView.as_view(), name="deconnexion"),
    path("moi/", MoiView.as_view(), name="moi"),
]
