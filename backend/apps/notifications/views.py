"""Vues des notifications push."""
from django.conf import settings
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.tenancy import secretariat_actif

from .models import AbonnementPush, Notification
from .serializers import AbonnementInputSerializer, NotificationSerializer
from .tasks import envoyer_notification_push


class ClePubliqueView(APIView):
    """GET /push/cle-publique/ — la clé VAPID publique pour l'abonnement navigateur."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"cle_publique": settings.VAPID_PUBLIC_KEY})


class AbonnementPushView(APIView):
    """POST/DELETE /push/abonnement/ — enregistre ou retire un appareil abonné."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        entree = AbonnementInputSerializer(data=request.data)
        entree.is_valid(raise_exception=True)
        donnees = entree.validated_data
        abonnement, _ = AbonnementPush.objects.update_or_create(
            endpoint=donnees["endpoint"],
            defaults={
                "utilisateur": request.user,
                "secretariat": secretariat_actif(request),
                "cle_p256dh": donnees["keys"]["p256dh"],
                "cle_auth": donnees["keys"]["auth"],
                "navigateur": donnees.get("navigateur", ""),
            },
        )
        return Response({"id": abonnement.id}, status=status.HTTP_201_CREATED)

    def delete(self, request):
        endpoint = request.data.get("endpoint", "")
        AbonnementPush.objects.filter(endpoint=endpoint, utilisateur=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class NotificationViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet,
):
    """Centre de notifications dans l'app (M6.5).

    Chaque utilisateur ne voit que ses propres notifications. Par défaut on ne
    renvoie pas les archivées ; `?archivees=1` les inclut, `?archivees=seules`
    ne renvoie qu'elles.
    """

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Notification.objects.filter(utilisateur=self.request.user)
        archivees = self.request.query_params.get("archivees")
        if archivees == "seules":
            return queryset.filter(archivee=True)
        if archivees not in ("1", "true"):
            queryset = queryset.filter(archivee=False)
        return queryset

    def list(self, request, *args, **kwargs):
        reponse = super().list(request, *args, **kwargs)
        non_lues = Notification.objects.filter(
            utilisateur=request.user, lu=False, archivee=False,
        ).count()
        # Compteur de la cloche fourni en même temps que la liste.
        if isinstance(reponse.data, dict):
            reponse.data["non_lues"] = non_lues
        else:
            reponse.data = {"resultats": reponse.data, "non_lues": non_lues}
        return reponse

    @action(detail=False, methods=["get"])
    def compteur(self, request):
        """GET /notifications/compteur/ — nombre de notifications non lues (cloche)."""
        non_lues = Notification.objects.filter(
            utilisateur=request.user, lu=False, archivee=False,
        ).count()
        return Response({"non_lues": non_lues})

    @action(detail=False, methods=["post"], url_path="tout-lire")
    def tout_lire(self, request):
        """POST /notifications/tout-lire/ — marque toutes les notifications comme lues."""
        maj = Notification.objects.filter(utilisateur=request.user, lu=False).update(lu=True)
        return Response({"marquees": maj})

    @action(detail=True, methods=["post"])
    def lire(self, request, pk=None):
        """POST /notifications/{id}/lire/ — marque une notification comme lue."""
        notif = self.get_object()
        if not notif.lu:
            notif.lu = True
            notif.save(update_fields=["lu"])
        return Response(self.get_serializer(notif).data)

    @action(detail=True, methods=["post"])
    def archiver(self, request, pk=None):
        """POST /notifications/{id}/archiver/ — archive une notification (la retire du centre)."""
        notif = self.get_object()
        notif.archivee = True
        notif.lu = True
        notif.save(update_fields=["archivee", "lu"])
        return Response(self.get_serializer(notif).data)


class TestPushView(APIView):
    """POST /push/test/ — envoie une notification de test à tous les appareils de l'utilisateur."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        abonnements = AbonnementPush.objects.filter(utilisateur=request.user)
        for abonnement in abonnements:
            envoyer_notification_push.delay(
                abonnement.id,
                "SigmaGestion",
                "Notification de test reçue 🎉",
                "/",
            )
        return Response({"envoyees": abonnements.count()})
