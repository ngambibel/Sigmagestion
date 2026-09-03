"""Routes des ventes."""
from rest_framework.routers import DefaultRouter

from .views import PrestationViewSet

router = DefaultRouter()
router.register("prestations", PrestationViewSet, basename="prestation")

urlpatterns = router.urls
