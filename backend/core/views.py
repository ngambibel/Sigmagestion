"""Vues du noyau : santé de l'infrastructure."""
from django.db import connection
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

import redis

from django.conf import settings


class SanteView(APIView):
    """Vérifie que la base de données et Redis répondent.

    GET /api/v1/sante/
    Réponse 200 si tout va bien, 503 si un composant est en panne.
    """

    permission_classes = []  # endpoint public de supervision

    def get(self, request):
        etat = {"base": self._verifier_base(), "redis": self._verifier_redis()}
        tout_ok = all(v == "ok" for v in etat.values())
        code = status.HTTP_200_OK if tout_ok else status.HTTP_503_SERVICE_UNAVAILABLE
        return Response(etat, status=code)

    @staticmethod
    def _verifier_base():
        try:
            with connection.cursor() as curseur:
                curseur.execute("SELECT 1")
                curseur.fetchone()
            return "ok"
        except Exception:  # noqa: BLE001
            return "erreur"

    @staticmethod
    def _verifier_redis():
        try:
            client = redis.from_url(settings.REDIS_URL)
            client.ping()
            return "ok"
        except Exception:  # noqa: BLE001
            return "erreur"
