"""Routes d'authentification et de profil."""
from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .employes import ChangerMotDePasseView, EmployeViewSet
from .views import ConnexionView, DeconnexionView, InscriptionView, MoiView

router = DefaultRouter()
router.register("employes", EmployeViewSet, basename="employe")

urlpatterns = [
    path("auth/inscription/", InscriptionView.as_view(), name="inscription"),
    path("auth/connexion/", ConnexionView.as_view(), name="connexion"),
    path("auth/rafraichir/", TokenRefreshView.as_view(), name="rafraichir"),
    path("auth/deconnexion/", DeconnexionView.as_view(), name="deconnexion"),
    path("moi/", MoiView.as_view(), name="moi"),
    path("moi/changer-mot-de-passe/", ChangerMotDePasseView.as_view(), name="changer-mot-de-passe"),
    *router.urls,
]
