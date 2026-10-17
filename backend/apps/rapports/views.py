"""Vues du tableau de bord (M7.1 propriétaire, M7.2 employé)."""
from django.core.cache import cache
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import EstGerantOuPlus
from core.tenancy import secretariat_actif

from .services import tableau_de_bord, tableau_de_bord_employe


class TableauDeBordEmployeView(APIView):
    """GET /tableau-de-bord/employe/ — vue limitée de l'employé (sans marges ni prix d'achat)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        secretariat = secretariat_actif(request)
        if secretariat is None:
            return Response({"detail": "Aucun secrétariat actif."}, status=400)
        return Response(tableau_de_bord_employe(request.user, secretariat))


class TableauDeBordView(APIView):
    """GET /tableau-de-bord/ — agrégats du jour et de la fenêtre glissante.

    Résultat mis en cache 60 s par secrétariat (les chiffres n'ont pas besoin
    d'être à la seconde, et la page est très consultée).
    """

    permission_classes = [EstGerantOuPlus]

    def get(self, request):
        secretariat = secretariat_actif(request)
        if secretariat is None:
            return Response({"detail": "Aucun secrétariat actif."}, status=400)

        cle = f"tableau-de-bord:{secretariat.id}"
        donnees = cache.get(cle)
        if donnees is None:
            donnees = tableau_de_bord(secretariat)
            cache.set(cle, donnees, 60)
        return Response(donnees)
