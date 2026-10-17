"""Vues du tableau de bord (M7.1 propriétaire, M7.2 employé)."""
from django.core.cache import cache
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import EstGerantOuPlus, EstProprietaire
from core.tenancy import secretariat_actif

from .exports import rapport_en_csv
from .rapports import RAPPORTS, parse_filtres
from .services import tableau_de_bord, tableau_de_bord_employe


class TableauDeBordEmployeView(APIView):
    """GET /tableau-de-bord/employe/ — vue limitée de l'employé (sans marges ni prix d'achat)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        secretariat = secretariat_actif(request)
        if secretariat is None:
            return Response({"detail": "Aucun secrétariat actif."}, status=400)
        return Response(tableau_de_bord_employe(request.user, secretariat))


class RapportView(APIView):
    """GET /rapports/{type}/ — rapports historiques (propriétaire).

    `type` ∈ {ventes, rentabilite, stock, caisse}. Filtres : date_debut, date_fin,
    service, employe, mode_reglement, statut. `?export=csv` renvoie un fichier CSV.
    """

    permission_classes = [EstProprietaire]

    def get(self, request, type_rapport):
        constructeur = RAPPORTS.get(type_rapport)
        if constructeur is None:
            return Response({"detail": "Rapport inconnu."}, status=404)
        secretariat = secretariat_actif(request)
        if secretariat is None:
            return Response({"detail": "Aucun secrétariat actif."}, status=400)

        filtres = parse_filtres(request.query_params)
        rapport = constructeur(secretariat, filtres)

        if request.query_params.get("export") == "csv":
            nom = f"{type_rapport}-{secretariat.code}"
            return rapport_en_csv(rapport, nom)
        return Response(rapport)


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
