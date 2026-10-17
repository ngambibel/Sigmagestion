"""Constructeurs de rapports historiques (M7.3).

Chaque rapport renvoie une structure homogène :
    {"titre", "colonnes": [{"cle", "libelle"}...], "lignes": [dict...], "totaux": dict}
ce qui permet un rendu de tableau générique côté front et un export CSV générique.
Réservé au propriétaire (marges et prix d'achat).
"""
from datetime import datetime, time

from django.db.models import DecimalField, F, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from apps.caisse.models import Depense, SessionCaisse
from apps.stocks.models import Consommable
from apps.ventes.models import LignePrestation, Prestation, StatutPrestation


def parse_filtres(params) -> dict:
    """Extrait et normalise les filtres communs depuis les query params."""
    filtres = {}
    for cle in ("date_debut", "date_fin"):
        valeur = params.get(cle)
        if valeur:
            try:
                filtres[cle] = datetime.strptime(valeur, "%Y-%m-%d").date()
            except ValueError:
                pass
    for cle in ("service", "employe"):
        valeur = params.get(cle)
        if valeur and valeur.isdigit():
            filtres[cle] = int(valeur)
    for cle in ("mode_reglement", "statut"):
        valeur = params.get(cle)
        if valeur:
            filtres[cle] = valeur
    return filtres


def _bornes(filtres):
    """Convertit date_debut/date_fin (locales, inclusives) en intervalle [debut, fin[ aware."""
    debut = fin = None
    if filtres.get("date_debut"):
        debut = timezone.make_aware(datetime.combine(filtres["date_debut"], time.min))
    if filtres.get("date_fin"):
        # fin de journée incluse → borne haute exclusive au lendemain 00:00
        fin = timezone.make_aware(
            datetime.combine(filtres["date_fin"], time.min)
        ) + timezone.timedelta(days=1)
    return debut, fin


def rapport_ventes(secretariat, filtres) -> dict:
    debut, fin = _bornes(filtres)
    qs = Prestation.objects.filter(secretariat=secretariat).select_related("employe")
    if debut:
        qs = qs.filter(cree_le__gte=debut)
    if fin:
        qs = qs.filter(cree_le__lt=fin)
    if filtres.get("mode_reglement"):
        qs = qs.filter(mode_paiement=filtres["mode_reglement"])
    if filtres.get("statut"):
        qs = qs.filter(statut=filtres["statut"])
    if filtres.get("employe"):
        qs = qs.filter(employe_id=filtres["employe"])
    if filtres.get("service"):
        qs = qs.filter(lignes__service_id=filtres["service"]).distinct()

    cout_expr = Coalesce(
        Sum(F("lignes__cout_unitaire") * F("lignes__quantite")), 0,
        output_field=DecimalField(max_digits=14, decimal_places=2),
    )
    qs = qs.annotate(cout_total=cout_expr).order_by("-cree_le")

    lignes = []
    ca_total = cout_total = nb_valides = 0
    for p in qs:
        cout = int(p.cout_total or 0)
        valide = p.statut == StatutPrestation.VALIDEE
        if valide:
            ca_total += p.montant_total
            cout_total += cout
            nb_valides += 1
        lignes.append({
            "numero": p.numero,
            "date": timezone.localtime(p.cree_le).strftime("%Y-%m-%d %H:%M"),
            "employe": p.employe.nom if p.employe else "",
            "mode": p.get_mode_paiement_display(),
            "statut": p.get_statut_display(),
            "montant": p.montant_total if valide else 0,
            "cout": cout if valide else 0,
            "marge": (p.montant_total - cout) if valide else 0,
        })

    return {
        "titre": "Rapport des ventes",
        "colonnes": [
            {"cle": "numero", "libelle": "N° ticket"},
            {"cle": "date", "libelle": "Date"},
            {"cle": "employe", "libelle": "Employé"},
            {"cle": "mode", "libelle": "Règlement"},
            {"cle": "statut", "libelle": "Statut"},
            {"cle": "montant", "libelle": "Montant"},
            {"cle": "cout", "libelle": "Coût"},
            {"cle": "marge", "libelle": "Marge"},
        ],
        "lignes": lignes,
        "totaux": {
            "nb_prestations": nb_valides,
            "ca_total": ca_total,
            "cout_total": cout_total,
            "marge_total": ca_total - cout_total,
        },
    }


def rapport_rentabilite(secretariat, filtres) -> dict:
    debut, fin = _bornes(filtres)
    lignes_qs = LignePrestation.objects.filter(
        prestation__secretariat=secretariat,
        prestation__statut=StatutPrestation.VALIDEE,
    )
    if debut:
        lignes_qs = lignes_qs.filter(prestation__cree_le__gte=debut)
    if fin:
        lignes_qs = lignes_qs.filter(prestation__cree_le__lt=fin)
    if filtres.get("service"):
        lignes_qs = lignes_qs.filter(service_id=filtres["service"])

    agg = (
        lignes_qs.values("nom_service")
        .annotate(
            qte=Sum("quantite"),
            ca=Sum(F("prix_unitaire") * F("quantite")),
            cout=Sum(F("cout_unitaire") * F("quantite")),
        )
        .order_by("-ca")
    )
    lignes = []
    ca_total = cout_total = 0
    for a in agg:
        ca = int(a["ca"] or 0)
        cout = int(a["cout"] or 0)
        marge = ca - cout
        ca_total += ca
        cout_total += cout
        lignes.append({
            "service": a["nom_service"],
            "quantite": a["qte"] or 0,
            "ca": ca,
            "cout": cout,
            "marge": marge,
            "marge_pct": round(marge / ca * 100) if ca else 0,
        })
    return {
        "titre": "Rapport de rentabilité",
        "colonnes": [
            {"cle": "service", "libelle": "Service"},
            {"cle": "quantite", "libelle": "Quantité"},
            {"cle": "ca", "libelle": "CA"},
            {"cle": "cout", "libelle": "Coût"},
            {"cle": "marge", "libelle": "Marge"},
            {"cle": "marge_pct", "libelle": "Marge %"},
        ],
        "lignes": lignes,
        "totaux": {
            "ca_total": ca_total,
            "cout_total": cout_total,
            "marge_total": ca_total - cout_total,
        },
    }


def rapport_stock(secretariat, filtres) -> dict:
    lignes = []
    valorisation_totale = 0
    for c in Consommable.objects.filter(secretariat=secretariat).order_by("nom"):
        valo = int(c.qte_stock * c.prix_achat)
        valorisation_totale += valo
        lignes.append({
            "consommable": c.nom,
            "unite": c.unite_mesure,
            "qte_stock": float(c.qte_stock),
            "prix_achat": c.prix_achat,
            "valorisation": valo,
            "seuil_alerte": float(c.seuil_alerte),
            "sous_seuil": "Oui" if c.qte_stock <= c.seuil_alerte else "",
        })
    return {
        "titre": "État et valorisation du stock",
        "colonnes": [
            {"cle": "consommable", "libelle": "Consommable"},
            {"cle": "unite", "libelle": "Unité"},
            {"cle": "qte_stock", "libelle": "En stock"},
            {"cle": "prix_achat", "libelle": "PU achat"},
            {"cle": "valorisation", "libelle": "Valorisation"},
            {"cle": "seuil_alerte", "libelle": "Seuil"},
            {"cle": "sous_seuil", "libelle": "Sous seuil"},
        ],
        "lignes": lignes,
        "totaux": {"valorisation_totale": valorisation_totale},
    }


def rapport_caisse(secretariat, filtres) -> dict:
    debut, fin = _bornes(filtres)
    qs = SessionCaisse.objects.filter(secretariat=secretariat).select_related("employe")
    if debut:
        qs = qs.filter(ouverte_le__gte=debut)
    if fin:
        qs = qs.filter(ouverte_le__lt=fin)
    if filtres.get("employe"):
        qs = qs.filter(employe_id=filtres["employe"])
    qs = qs.order_by("-ouverte_le")

    lignes = []
    ecart_total = 0
    for s in qs:
        ecart = s.ecart or 0
        ecart_total += ecart
        lignes.append({
            "employe": s.employe.nom if s.employe else "",
            "ouverte_le": timezone.localtime(s.ouverte_le).strftime("%Y-%m-%d %H:%M"),
            "fermee_le": timezone.localtime(s.cloturee_le).strftime("%Y-%m-%d %H:%M") if s.cloturee_le else "",
            "fond_initial": s.fond_initial,
            "theorique": s.montant_theorique if s.montant_theorique is not None else "",
            "compte": s.montant_compte if s.montant_compte is not None else "",
            "ecart": ecart,
            "statut": s.get_statut_display(),
        })

    # Dépenses par catégorie sur la période.
    dep_qs = Depense.objects.filter(secretariat=secretariat)
    if debut:
        dep_qs = dep_qs.filter(cree_le__gte=debut)
    if fin:
        dep_qs = dep_qs.filter(cree_le__lt=fin)
    depenses_par_categorie = {
        d["categorie"]: d["total"]
        for d in dep_qs.values("categorie").annotate(total=Sum("montant"))
    }

    return {
        "titre": "Rapport de caisse",
        "colonnes": [
            {"cle": "employe", "libelle": "Employé"},
            {"cle": "ouverte_le", "libelle": "Ouverture"},
            {"cle": "fermee_le", "libelle": "Clôture"},
            {"cle": "fond_initial", "libelle": "Fond"},
            {"cle": "theorique", "libelle": "Théorique"},
            {"cle": "compte", "libelle": "Compté"},
            {"cle": "ecart", "libelle": "Écart"},
            {"cle": "statut", "libelle": "Statut"},
        ],
        "lignes": lignes,
        "totaux": {
            "nb_sessions": len(lignes),
            "ecart_total": ecart_total,
            "depenses_total": sum(depenses_par_categorie.values()),
            "depenses_par_categorie": depenses_par_categorie,
        },
    }


RAPPORTS = {
    "ventes": rapport_ventes,
    "rentabilite": rapport_rentabilite,
    "stock": rapport_stock,
    "caisse": rapport_caisse,
}
