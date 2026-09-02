"""Vues de la caisse."""
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.comptes.models import Role
from core.tenancy import TenantQuerySetMixin, secretariat_actif

from .models import SessionCaisse, StatutSession
from .serializers import SessionCaisseSerializer


class SessionCaisseViewSet(
    TenantQuerySetMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """Ouverture et consultation des sessions de caisse.

    - Tout membre peut ouvrir SA session (RG-11 : une seule ouverte à la fois).
    - Un employé ne voit que ses sessions ; propriétaire/gérant voient tout le secrétariat.
    """

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

        # RG-11 : refuser une deuxième session ouverte pour cet utilisateur.
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
        sortie = self.get_serializer(session)
        return Response(sortie.data, status=status.HTTP_201_CREATED)

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
        return Response(self.get_serializer(session).data)
