"""Routes des stocks."""
from rest_framework.routers import DefaultRouter

from .views import ConsommableViewSet

router = DefaultRouter()
router.register("consommables", ConsommableViewSet, basename="consommable")

urlpatterns = router.urls
