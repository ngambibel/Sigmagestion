"""Routes des secrétariats."""
from rest_framework.routers import DefaultRouter

from .views import SecretariatViewSet

router = DefaultRouter()
router.register("secretariats", SecretariatViewSet, basename="secretariat")

urlpatterns = router.urls
