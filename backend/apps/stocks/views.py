"""Vues des stocks."""
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.permissions import EstGerantOuPlus, EstProprietaire
from core.tenancy import TenantQuerySetMixin

from .models import Consommable
from .serializers import (
    ConsommableSerializer,
    EntreeStockSerializer,
    MouvementStockSerializer,
)
from .services import enregistrer_entree_stock


class ConsommableViewSet(TenantQuerySetMixin, viewsets.ModelViewSet):
    """CRUD des consommables, cloisonné au secrétariat actif."""

    serializer_class = ConsommableSerializer
    queryset = Consommable.objects.all()

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [EstProprietaire()]
        if self.action == "entree_stock":
            return [EstGerantOuPlus()]  # gérant autorisé à réapprovisionner
        return [IsAuthenticated()]

    @action(detail=False, methods=["get"])
    def alertes(self, request):
        """GET /consommables/alertes/ — les consommables actifs sous leur seuil."""
        sous_seuil = [c for c in self.get_queryset().filter(actif=True) if c.sous_seuil]
        return Response(self.get_serializer(sous_seuil, many=True).data)

    @action(detail=True, methods=["post"], url_path="entree-stock")
    def entree_stock(self, request, pk=None):
        """POST /consommables/{id}/entree-stock/ — réapprovisionnement + CUMP."""
        consommable = self.get_object()
        entree = EntreeStockSerializer(data=request.data)
        entree.is_valid(raise_exception=True)

        mouvement = enregistrer_entree_stock(
            consommable=consommable,
            quantite=entree.validated_data["quantite"],
            prix_total_lot=entree.validated_data["prix_total_lot"],
            fournisseur=entree.validated_data.get("fournisseur", ""),
            motif=entree.validated_data.get("motif", ""),
            auteur=request.user,
        )
        consommable.refresh_from_db()  # la couche métier a mis à jour une autre instance
        return Response(
            {
                "mouvement": MouvementStockSerializer(mouvement).data,
                "consommable": ConsommableSerializer(consommable).data,
            },
            status=status.HTTP_201_CREATED,
        )
