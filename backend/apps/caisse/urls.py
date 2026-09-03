"""Routes de la caisse."""
from rest_framework.routers import DefaultRouter

from .views import DepenseViewSet, SessionCaisseViewSet

router = DefaultRouter()
router.register("sessions-caisse", SessionCaisseViewSet, basename="session-caisse")
router.register("depenses", DepenseViewSet, basename="depense")

urlpatterns = router.urls
