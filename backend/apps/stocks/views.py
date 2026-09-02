"""Vues des stocks."""
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

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

    @action(detail=False, methods=["get"])
    def alertes(self, request):
        """GET /consommables/alertes/ — les consommables actifs sous leur seuil."""
        sous_seuil = [c for c in self.get_queryset().filter(actif=True) if c.sous_seuil]
        return Response(self.get_serializer(sous_seuil, many=True).data)
