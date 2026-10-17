"""Agrégations du tableau de bord propriétaire (M7.1).

La logique vit ici (couche service) ; la vue ne fait qu'orchestrer et mettre en cache.
Réutilise `agreger_ca` de l'app ventes pour les totaux du jour / de la veille.
"""
from datetime import timedelta

from django.db.models import Count, F, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone

from apps.stocks.models import Consommable
from apps.ventes.models import LignePrestation, Prestation, StatutPrestation
from apps.ventes.services import agreger_ca

FENETRE_JOURS = 30


def _variation(courant: int, reference: int):
    """Variation en % vs la veille (None si pas de référence)."""
    if reference <= 0:
        return None
    return round((courant - reference) / reference * 100)


def tableau_de_bord(secretariat) -> dict:
    maintenant = timezone.localtime()
    debut_jour = maintenant.replace(hour=0, minute=0, second=0, microsecond=0)
    debut_fenetre = debut_jour - timedelta(days=FENETRE_JOURS - 1)

    # --- CA du jour vs même tranche la veille ---
    jour = agreger_ca(secretariat, debut_jour, maintenant)
    veille = agreger_ca(secretariat, debut_jour - timedelta(days=1), maintenant - timedelta(days=1))

    ventes = Prestation.objects.filter(
        secretariat=secretariat, statut=StatutPrestation.VALIDEE,
    )

    # --- Série du CA sur 30 jours (jours sans vente complétés à 0) ---
    brut = (
        ventes.filter(cree_le__gte=debut_fenetre)
        .annotate(j=TruncDate("cree_le"))
        .values("j")
        .annotate(ca=Sum("montant_total"))
    )
    par_date = {ligne["j"]: ligne["ca"] or 0 for ligne in brut}
    serie_30j = []
    for i in range(FENETRE_JOURS):
        jour_i = (debut_fenetre + timedelta(days=i)).date()
        serie_30j.append({"date": jour_i.isoformat(), "ca": par_date.get(jour_i, 0)})

    # --- Répartition par service sur la fenêtre (barres + top 5) ---
    lignes = LignePrestation.objects.filter(
        prestation__in=ventes.filter(cree_le__gte=debut_fenetre),
    )
    par_service = list(
        lignes.values("nom_service")
        .annotate(ca=Sum(F("prix_unitaire") * F("quantite")))
        .order_by("-ca")
    )

    # --- Performance par employé sur la fenêtre ---
    par_employe = list(
        ventes.filter(cree_le__gte=debut_fenetre)
        .values("employe__nom")
        .annotate(ca=Sum("montant_total"), nb=Count("id"))
        .order_by("-ca")
    )
    par_employe = [
        {"employe": e["employe__nom"], "ca": e["ca"] or 0, "nb": e["nb"]} for e in par_employe
    ]

    # --- Consommables sous le seuil d'alerte ---
    sous_seuil = [
        {
            "id": c.id,
            "nom": c.nom,
            "qte_stock": str(c.qte_stock),
            "seuil_alerte": str(c.seuil_alerte),
            "unite_mesure": c.unite_mesure,
        }
        for c in Consommable.objects.filter(
            secretariat=secretariat, actif=True, qte_stock__lte=F("seuil_alerte"),
        ).order_by("qte_stock")
    ]

    return {
        "ca_jour": jour["ca"],
        "ca_veille": veille["ca"],
        "variation_pct": _variation(jour["ca"], veille["ca"]),
        "nb_prestations_jour": jour["nb_prestations"],
        "marge_jour": jour["marge"],
        "serie_30j": serie_30j,
        "par_service": par_service,
        "top_services": par_service[:5],
        "par_employe": par_employe,
        "consommables_sous_seuil": sous_seuil,
    }
