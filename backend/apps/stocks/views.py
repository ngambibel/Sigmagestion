"""Vues des stocks."""
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.permissions import EstGerantOuPlus, EstProprietaire
from core.tenancy import TenantQuerySetMixin

from .models import Consommable, MouvementStock, TypeMouvement
from .serializers import (
    AjustementSerializer,
    ConsommableSerializer,
    EntreeStockSerializer,
    MouvementStockSerializer,
)
from .services import enregistrer_ajustement, enregistrer_entree_stock


class ConsommableViewSet(TenantQuerySetMixin, viewsets.ModelViewSet):
    """CRUD des consommables, cloisonné au secrétariat actif."""

    serializer_class = ConsommableSerializer
    queryset = Consommable.objects.all()

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy", "ajustement"):
            return [EstProprietaire()]
        if self.action == "entree_stock":
            return [EstGerantOuPlus()]  # gérant autorisé à réapprovisionner
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        super().perform_create(serializer)  # rattache au secrétariat + sauvegarde
        # Trace du stock initial déclaré, pour la cohérence du journal.
        consommable = serializer.instance
        if consommable.qte_stock and consommable.qte_stock > 0:
            MouvementStock.objects.create(
                secretariat=consommable.secretariat,
                consommable=consommable,
                type=TypeMouvement.AJUSTEMENT,
                quantite=consommable.qte_stock,
                stock_avant=0,
                stock_apres=consommable.qte_stock,
                motif="Stock initial",
                auteur=self.request.user,
            )

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

    @action(detail=True, methods=["post"])
    def ajustement(self, request, pk=None):
        """POST /consommables/{id}/ajustement/ — correction avec motif obligatoire."""
        consommable = self.get_object()
        ajust = AjustementSerializer(data=request.data)
        ajust.is_valid(raise_exception=True)
        try:
            mouvement = enregistrer_ajustement(
                consommable=consommable,
                quantite_delta=ajust.validated_data["quantite_delta"],
                motif=ajust.validated_data["motif"],
                auteur=request.user,
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        consommable.refresh_from_db()

        from apps.audit.models import ActionAudit
        from apps.audit.services import tracer

        tracer(
            action=ActionAudit.STOCK_AJUSTE, instance=consommable, auteur=request.user,
            avant={"stock": str(mouvement.stock_avant)},
            apres={"stock": str(mouvement.stock_apres), "motif": mouvement.motif},
            request=request, objet_repr=consommable.nom,
        )
        return Response(
            {
                "mouvement": MouvementStockSerializer(mouvement).data,
                "consommable": ConsommableSerializer(consommable).data,
            },
            status=status.HTTP_201_CREATED,
        )


class MouvementStockViewSet(TenantQuerySetMixin, viewsets.ReadOnlyModelViewSet):
    """GET /mouvements-stock/ — journal des mouvements, filtrable (gérant+)."""

    serializer_class = MouvementStockSerializer
    queryset = MouvementStock.objects.select_related("consommable", "auteur").all()
    permission_classes = [EstGerantOuPlus]

    def get_queryset(self):
        queryset = super().get_queryset()
        consommable = self.request.query_params.get("consommable")
        type_mvt = self.request.query_params.get("type")
        if consommable:
            queryset = queryset.filter(consommable_id=consommable)
        if type_mvt:
            queryset = queryset.filter(type=type_mvt)
        return queryset
