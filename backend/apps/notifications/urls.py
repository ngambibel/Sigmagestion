"""Routes des notifications push."""
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    AbonnementPushView,
    ClePubliqueView,
    NotificationViewSet,
    TestPushView,
)

router = DefaultRouter()
router.register("notifications", NotificationViewSet, basename="notification")

urlpatterns = [
    path("push/cle-publique/", ClePubliqueView.as_view(), name="push-cle-publique"),
    path("push/abonnement/", AbonnementPushView.as_view(), name="push-abonnement"),
    path("push/test/", TestPushView.as_view(), name="push-test"),
    *router.urls,
]
