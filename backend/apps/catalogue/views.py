"""Vues du catalogue."""
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from core.permissions import EstProprietaire
from core.tenancy import TenantQuerySetMixin

from .models import Service
from .serializers import ServiceSerializer


class ServiceViewSet(TenantQuerySetMixin, viewsets.ModelViewSet):
    """CRUD des services, cloisonné au secrétariat actif."""

    serializer_class = ServiceSerializer
    queryset = Service.objects.all()

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [EstProprietaire()]
        return [IsAuthenticated()]
