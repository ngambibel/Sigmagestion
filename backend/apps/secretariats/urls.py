"""Routes des secrétariats."""
from django.urls import path
from rest_framework.routers import DefaultRouter

from .onboarding import ModelesOnboardingView
from .views import SecretariatViewSet

router = DefaultRouter()
router.register("secretariats", SecretariatViewSet, basename="secretariat")

urlpatterns = [
    path("onboarding/modeles/", ModelesOnboardingView.as_view(), name="onboarding-modeles"),
    *router.urls,
]
