"""Vues de la caisse."""
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.comptes.models import Role
from core.permissions import EstGerantOuPlus
from core.tenancy import TenantQuerySetMixin, secretariat_actif

from .models import Depense, SessionCaisse, StatutSession
from .serializers import ClotureSerializer, DepenseSerializer, SessionCaisseSerializer
from .services import CaisseError, cloturer_session, montant_theorique_session


class SessionCaisseViewSet(
    TenantQuerySetMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """Ouverture, consultation et clôture des sessions de caisse."""

    serializer_class = SessionCaisseSerializer
    queryset = SessionCaisse.objects.select_related("employe").all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        utilisateur = self.request.user
        if utilisateur.role == Role.EMPLOYE:
            return queryset.filter(employe=utilisateur)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if SessionCaisse.objects.filter(
            employe=request.user, statut=StatutSession.OUVERTE
        ).exists():
            return Response(
                {"detail": "Vous avez déjà une session de caisse ouverte."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        session = SessionCaisse.objects.create(
            secretariat=secretariat_actif(request),
            employe=request.user,
            fond_initial=serializer.validated_data.get("fond_initial", 0),
        )
        from apps.notifications.tasks import notifier_session

        notifier_session(session, ouverture=True)
        return Response(self.get_serializer(session).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"])
    def active(self, request):
        """GET /sessions-caisse/active/ — la session ouverte de l'utilisateur, ou null."""
        session = (
            SessionCaisse.objects.filter(employe=request.user, statut=StatutSession.OUVERTE)
            .select_related("employe")
            .first()
        )
        if session is None:
            return Response(None)
        donnees = self.get_serializer(session).data
        donnees["montant_theorique_estime"] = montant_theorique_session(session)
        return Response(donnees)

    @action(detail=True, methods=["post"])
    def cloturer(self, request, pk=None):
        """POST /sessions-caisse/{id}/cloturer/ — clôture avec écart (RG-12)."""
        session = self.get_object()
        cloture = ClotureSerializer(data=request.data)
        cloture.is_valid(raise_exception=True)
        try:
            session = cloturer_session(
                session,
                montant_compte=cloture.validated_data["montant_compte"],
                commentaire=cloture.validated_data.get("commentaire", ""),
            )
        except CaisseError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(self.get_serializer(session).data)


class DepenseViewSet(
    TenantQuerySetMixin,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """Dépenses rattachées à la session ouverte de l'utilisateur (gérant+)."""

    serializer_class = DepenseSerializer
    queryset = Depense.objects.select_related("auteur").all()

    def get_permissions(self):
        if self.action == "create":
            return [EstGerantOuPlus()]
        return [IsAuthenticated()]

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
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(
            secretariat=secretariat_actif(request), session=session, auteur=request.user,
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)
