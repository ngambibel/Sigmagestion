"""Vues des clients et créances (M9)."""
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.ventes.models import Prestation, StatutPrestation
from apps.ventes.serializers import PrestationSerializer
from core.permissions import EstGerantOuPlus
from core.tenancy import TenantQuerySetMixin

from .models import Client
from .serializers import ClientSerializer, ReglementSerializer
from .services import ClientError, enregistrer_reglement


class ClientViewSet(
    TenantQuerySetMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """Fiches clients et créances. Cloisonné au secrétariat actif.

    Création possible au comptoir (employé) pour une vente à crédit ; les
    règlements (encaissement d'une créance) sont réservés au gérant/propriétaire.
    """

    serializer_class = ClientSerializer
    queryset = Client.objects.all()

    def get_permissions(self):
        if self.action in ("reglement",):
            return [EstGerantOuPlus()]
        return [IsAuthenticated()]

    @action(detail=True, methods=["post"])
    def reglement(self, request, pk=None):
        """POST /clients/{id}/reglement/ — enregistre un règlement, diminue l'encours."""
        client = self.get_object()
        try:
            reglement, client = enregistrer_reglement(
                client=client,
                montant=request.data.get("montant", 0),
                auteur=request.user,
                commentaire=request.data.get("commentaire", ""),
            )
        except (ClientError, ValueError, TypeError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            "reglement": ReglementSerializer(reglement).data,
            "client": ClientSerializer(client).data,
        })

    @action(detail=True, methods=["get"])
    def historique(self, request, pk=None):
        """GET /clients/{id}/historique/ — ventes à crédit et règlements du client."""
        client = self.get_object()
        prestations = (
            Prestation.objects.filter(client=client)
            .select_related("employe").prefetch_related("lignes").order_by("-cree_le")
        )
        return Response({
            "client": ClientSerializer(client).data,
            "prestations": PrestationSerializer(prestations, many=True).data,
            "reglements": ReglementSerializer(client.reglements.all(), many=True).data,
            "credits_non_regles": client.prestations.filter(
                statut=StatutPrestation.VALIDEE,
            ).count(),
        })
