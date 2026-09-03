"""Routes des notifications push."""
from django.urls import path

from .views import AbonnementPushView, ClePubliqueView, TestPushView

urlpatterns = [
    path("push/cle-publique/", ClePubliqueView.as_view(), name="push-cle-publique"),
    path("push/abonnement/", AbonnementPushView.as_view(), name="push-abonnement"),
    path("push/test/", TestPushView.as_view(), name="push-test"),
]
