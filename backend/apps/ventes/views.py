"""Vues des ventes."""
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.caisse.models import SessionCaisse, StatutSession
from apps.stocks.serializers import ConsommableSerializer
from core.permissions import EstGerantOuPlus
from core.tenancy import TenantQuerySetMixin

from .models import Prestation
from .serializers import PrestationCreationSerializer, PrestationSerializer
from .services import VenteError, annuler_prestation, enregistrer_prestation


class PrestationViewSet(
    TenantQuerySetMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Enregistrement et consultation des prestations."""

    serializer_class = PrestationSerializer
    queryset = Prestation.objects.select_related("employe").prefetch_related("lignes").all()
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        session = (
            SessionCaisse.objects.filter(employe=request.user, statut=StatutSession.OUVERTE)
            .first()
        )
        if session is None:
            return Response(
                {"detail": "Ouvrez d'abord une session de caisse."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        entree = PrestationCreationSerializer(data=request.data)
        entree.is_valid(raise_exception=True)

        try:
            prestation, alertes = enregistrer_prestation(
                session=session,
                lignes_saisie=entree.validated_data["lignes"],
                mode_paiement=entree.validated_data["mode_paiement"],
                remise=entree.validated_data.get("remise", 0),
                montant_recu=entree.validated_data.get("montant_recu"),
                nom_client=entree.validated_data.get("nom_client", ""),
                auteur=request.user,
            )
        except VenteError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "prestation": PrestationSerializer(prestation).data,
                "alertes_stock": ConsommableSerializer(alertes, many=True).data,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], permission_classes=[EstGerantOuPlus])
    def annuler(self, request, pk=None):
        """POST /prestations/{id}/annuler/ — annulation avec contre-passation (gérant+)."""
        prestation = self.get_object()
        try:
            prestation = annuler_prestation(
                prestation=prestation, motif=request.data.get("motif", ""), auteur=request.user,
            )
        except VenteError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(PrestationSerializer(prestation).data)
