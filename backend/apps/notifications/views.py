"""Vues des notifications push."""
from django.conf import settings
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.tenancy import secretariat_actif

from .models import AbonnementPush
from .serializers import AbonnementInputSerializer
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
