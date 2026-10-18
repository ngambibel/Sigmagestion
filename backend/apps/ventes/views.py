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

        # Résolution du client (crédit), cloisonné au secrétariat de la session.
        client = None
        client_id = entree.validated_data.get("client")
        if client_id:
            from apps.clients.models import Client

            client = Client.objects.filter(id=client_id, secretariat=session.secretariat).first()
            if client is None:
                return Response(
                    {"detail": "Client introuvable dans ce secrétariat."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        try:
            prestation, alertes = enregistrer_prestation(
                session=session,
                lignes_saisie=entree.validated_data["lignes"],
                mode_paiement=entree.validated_data["mode_paiement"],
                remise=entree.validated_data.get("remise", 0),
                montant_recu=entree.validated_data.get("montant_recu"),
                nom_client=entree.validated_data.get("nom_client", ""),
                client=client,
                client_uuid=entree.validated_data.get("client_uuid"),
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

    @action(detail=False, methods=["post"])
    def synchroniser(self, request):
        """POST /prestations/synchroniser/ — envoi par lots des ventes hors ligne.

        Idempotent par `client_uuid` (aucun doublon au rejeu). Le serveur fait
        autorité sur le stock : une vente qui le ferait passer en négatif est
        acceptée, avec une alerte de régularisation.
        """
        session = (
            SessionCaisse.objects.filter(employe=request.user, statut=StatutSession.OUVERTE)
            .first()
        )
        if session is None:
            return Response(
                {"detail": "Ouvrez une session de caisse pour synchroniser."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ventes = request.data.get("ventes", [])
        resultats = []
        for item in ventes:
            entree = PrestationCreationSerializer(data=item)
            if not entree.is_valid():
                resultats.append({
                    "client_uuid": item.get("client_uuid"),
                    "statut": "erreur", "detail": "Données invalides.",
                })
                continue
            donnees = entree.validated_data
            uuid = donnees.get("client_uuid")
            deja = bool(uuid) and Prestation.objects.filter(client_uuid=uuid).exists()

            client = None
            if donnees.get("client"):
                from apps.clients.models import Client

                client = Client.objects.filter(
                    id=donnees["client"], secretariat=session.secretariat,
                ).first()

            try:
                prestation, alertes = enregistrer_prestation(
                    session=session,
                    lignes_saisie=donnees["lignes"],
                    mode_paiement=donnees["mode_paiement"],
                    remise=donnees.get("remise", 0),
                    montant_recu=donnees.get("montant_recu"),
                    client=client,
                    client_uuid=uuid,
                    auteur=request.user,
                    forcer_stock=True,
                )
            except VenteError as exc:
                resultats.append({"client_uuid": str(uuid), "statut": "erreur", "detail": str(exc)})
                continue

            resultats.append({
                "client_uuid": str(uuid),
                "statut": "doublon" if deja else "ok",
                "prestation": PrestationSerializer(prestation).data,
                "alertes_stock": ConsommableSerializer(alertes, many=True).data,
            })
        return Response({"resultats": resultats})

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

        from apps.audit.models import ActionAudit
        from apps.audit.services import tracer

        tracer(
            action=ActionAudit.PRESTATION_ANNULEE, instance=prestation, auteur=request.user,
            avant={"statut": "validee"},
            apres={"statut": "annulee", "motif": prestation.motif_annulation,
                   "montant": prestation.montant_total},
            request=request, objet_repr=prestation.numero,
        )
        return Response(PrestationSerializer(prestation).data)
