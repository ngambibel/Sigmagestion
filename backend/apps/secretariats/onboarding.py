"""Endpoint fournissant le catalogue de démarrage pour l'assistant d'installation."""
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalogue.donnees import SERVICES_DEFAUT
from apps.stocks.donnees import CONSOMMABLES_DEFAUT


class ModelesOnboardingView(APIView):
    """GET /onboarding/modeles/ — services et consommables proposés par défaut.

    Le propriétaire coche ceux qu'il veut, ajuste prix et stocks, puis crée
    ses services / consommables via les endpoints dédiés.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "services": SERVICES_DEFAUT,
                "consommables": CONSOMMABLES_DEFAUT,
            }
        )
