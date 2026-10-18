"""Routes du journal d'audit."""
from rest_framework.routers import DefaultRouter

from .views import JournalAuditViewSet

router = DefaultRouter()
router.register("audit", JournalAuditViewSet, basename="audit")

urlpatterns = [*router.urls]
