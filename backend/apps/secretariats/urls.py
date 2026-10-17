"""Routes des secrétariats."""
from django.urls import path
from rest_framework.routers import DefaultRouter

from .onboarding import ModelesOnboardingView
from .views import ParametresNotificationView, PlagesHorairesView, SecretariatViewSet

router = DefaultRouter()
router.register("secretariats", SecretariatViewSet, basename="secretariat")

urlpatterns = [
    path("onboarding/modeles/", ModelesOnboardingView.as_view(), name="onboarding-modeles"),
    path(
        "secretariats/<int:secretariat_id>/plages-horaires/",
        PlagesHorairesView.as_view(), name="secretariat-plages-horaires",
    ),
    path(
        "secretariats/<int:secretariat_id>/parametres-notification/",
        ParametresNotificationView.as_view(), name="secretariat-parametres-notification",
    ),
    *router.urls,
]
