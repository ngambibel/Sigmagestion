"""Vues des stocks."""
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from core.permissions import EstProprietaire
from core.tenancy import TenantQuerySetMixin

from .models import Consommable
from .serializers import ConsommableSerializer


class ConsommableViewSet(TenantQuerySetMixin, viewsets.ModelViewSet):
    """CRUD des consommables, cloisonné au secrétariat actif."""

    serializer_class = ConsommableSerializer
    queryset = Consommable.objects.all()

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [EstProprietaire()]
        return [IsAuthenticated()]
