"""Routes de la caisse."""
from rest_framework.routers import DefaultRouter

from .views import SessionCaisseViewSet

router = DefaultRouter()
router.register("sessions-caisse", SessionCaisseViewSet, basename="session-caisse")

urlpatterns = router.urls
