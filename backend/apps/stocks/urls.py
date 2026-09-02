"""Routes des stocks."""
from rest_framework.routers import DefaultRouter

from .views import ConsommableViewSet, MouvementStockViewSet

router = DefaultRouter()
router.register("consommables", ConsommableViewSet, basename="consommable")
router.register("mouvements-stock", MouvementStockViewSet, basename="mouvement")

urlpatterns = router.urls
