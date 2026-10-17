"""Enregistrement d'une prestation — le cœur transactionnel du produit (RG-04).

Tout se joue dans UNE transaction atomique : figer les prix/coûts, décrémenter
le stock via la nomenclature, tracer les mouvements, évaluer les seuils.
Verrouillage pessimiste (`select_for_update`) sur le secrétariat (numérotation)
et sur les consommables (concurrence de saisie).
"""
from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction
from django.db.models import Count, F, Sum
from django.utils import timezone

from apps.caisse.models import StatutSession
from apps.catalogue.models import Service
from apps.secretariats.models import Secretariat
from apps.stocks.models import Consommable, MouvementStock, TypeMouvement

from .models import LignePrestation, ModePaiement, Prestation, StatutPrestation


class VenteError(Exception):
    """Erreur métier lors d'une vente (renvoyée en 400)."""


def _generer_numero(secretariat) -> str:
    prefixe = f"{secretariat.code}-{timezone.localdate().strftime('%Y%m%d')}"
    rang = (
        Prestation.objects.filter(secretariat=secretariat, numero__startswith=prefixe).count() + 1
    )
    return f"{prefixe}-{rang:04d}"


@transaction.atomic
def enregistrer_prestation(
    *, session, lignes_saisie, mode_paiement, remise=0, montant_recu=None,
    nom_client="", auteur=None,
):
    if session.statut != StatutSession.OUVERTE:
        raise VenteError("La session de caisse n'est pas ouverte.")

    nom_client = (nom_client or "").strip()
    if mode_paiement == ModePaiement.CREDIT and not nom_client:
        raise VenteError("Le nom du client est requis pour une vente à crédit.")

    # Verrou secrétariat : sérialise la numérotation des tickets.
    secretariat = Secretariat.objects.select_for_update().get(pk=session.secretariat_id)

    # 1. Figer les lignes (prix + coût de revient) et cumuler les besoins en stock.
    besoins: dict[int, Decimal] = {}
    lignes_data = []
    sous_total = 0
    for item in lignes_saisie:
        try:
            service = Service.objects.get(id=item["service"], secretariat=secretariat)
        except Service.DoesNotExist as exc:
            raise VenteError("Service introuvable dans ce secrétariat.") from exc
        quantite = int(item["quantite"])
        if quantite <= 0:
            continue
        cout = Decimal("0")
        for nl in service.lignes_nomenclature.select_related("consommable").all():
            cout += nl.qte_par_unite * nl.consommable.prix_achat
            besoins[nl.consommable_id] = besoins.get(nl.consommable_id, Decimal("0")) + (
                nl.qte_par_unite * quantite
            )
        cout_unitaire = int(cout.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        sous_total += service.prix * quantite
        lignes_data.append(
            {"service": service, "nom": service.nom, "prix": service.prix,
             "quantite": quantite, "cout_unitaire": cout_unitaire}
        )

    if not lignes_data:
        raise VenteError("Le ticket est vide.")

    remise = int(remise or 0)
    montant_total = max(0, sous_total - remise)

    # 2. Paiement.
    montant_recu_val = None
    monnaie = None
    if mode_paiement == ModePaiement.ESPECES:
        if montant_recu is None:
            raise VenteError("Le montant reçu est requis pour un paiement en espèces.")
        montant_recu_val = int(montant_recu)
        if montant_recu_val < montant_total:
            raise VenteError("Le montant reçu est inférieur au total.")
        monnaie = montant_recu_val - montant_total

    # 3. Verrouiller les consommables et vérifier le stock.
    consommables = {
        c.id: c
        for c in Consommable.objects.select_for_update().filter(id__in=list(besoins.keys()))
    }
    if not secretariat.autoriser_stock_negatif:
        manquants = [
            f"{consommables[cid].nom} (reste {consommables[cid].qte_stock}, besoin {besoin})"
            for cid, besoin in besoins.items()
            if consommables[cid].qte_stock < besoin
        ]
        if manquants:
            raise VenteError("Stock insuffisant : " + " ; ".join(manquants))

    # 4. Créer la prestation et ses lignes.
    prestation = Prestation.objects.create(
        secretariat=secretariat, session=session, numero=_generer_numero(secretariat),
        employe=auteur, mode_paiement=mode_paiement, remise=remise,
        montant_total=montant_total, montant_recu=montant_recu_val, monnaie_rendue=monnaie,
        nom_client=nom_client,
    )
    LignePrestation.objects.bulk_create(
        [
            LignePrestation(
                prestation=prestation, service=ld["service"], nom_service=ld["nom"],
                prix_unitaire=ld["prix"], quantite=ld["quantite"], cout_unitaire=ld["cout_unitaire"],
            )
            for ld in lignes_data
        ]
    )

    # 5. Décrémenter le stock, tracer les mouvements, collecter les alertes de seuil.
    alertes = []
    for cid, besoin in besoins.items():
        c = consommables[cid]
        stock_avant = c.qte_stock
        stock_apres = stock_avant - besoin
        c.qte_stock = stock_apres
        c.save(update_fields=["qte_stock", "modifie_le"])
        MouvementStock.objects.create(
            secretariat=secretariat, consommable=c, type=TypeMouvement.SORTIE_VENTE,
            quantite=-besoin, stock_avant=stock_avant, stock_apres=stock_apres,
            prestation=prestation, auteur=auteur, motif=f"Vente {prestation.numero}",
        )
        if c.actif and stock_apres <= c.seuil_alerte:
            alertes.append(c)

    return prestation, alertes


@transaction.atomic
def annuler_prestation(*, prestation, motif, auteur=None):
    """Annule une prestation sans la supprimer (RG-03) : contre-passe le stock.

    Chaque sortie de vente est compensée par un mouvement ANNULATION qui
    réinjecte la quantité. La prestation passe au statut ANNULEE.
    """
    motif = (motif or "").strip()
    if not motif:
        raise VenteError("Un motif est obligatoire pour annuler une vente.")

    prestation = Prestation.objects.select_for_update().get(pk=prestation.pk)
    if prestation.statut == StatutPrestation.ANNULEE:
        raise VenteError("Cette prestation est déjà annulée.")

    sorties = prestation.mouvements_stock.filter(type=TypeMouvement.SORTIE_VENTE)
    for mouvement in sorties:
        consommable = Consommable.objects.select_for_update().get(pk=mouvement.consommable_id)
        quantite_retour = -mouvement.quantite  # la sortie était négative → retour positif
        stock_avant = consommable.qte_stock
        stock_apres = stock_avant + quantite_retour
        consommable.qte_stock = stock_apres
        consommable.save(update_fields=["qte_stock", "modifie_le"])
        MouvementStock.objects.create(
            secretariat=prestation.secretariat, consommable=consommable,
            type=TypeMouvement.ANNULATION, quantite=quantite_retour,
            stock_avant=stock_avant, stock_apres=stock_apres,
            prestation=prestation, auteur=auteur,
            motif=f"Annulation {prestation.numero} : {motif}",
        )

    prestation.statut = StatutPrestation.ANNULEE
    prestation.annulee_le = timezone.now()
    prestation.motif_annulation = motif
    prestation.save(update_fields=["statut", "annulee_le", "motif_annulation"])
    return prestation


def agreger_ca(secretariat, debut, fin) -> dict:
    """Agrège les ventes VALIDÉES d'un secrétariat sur l'intervalle [debut, fin[.

    Réutilisable par les notifications de CA (phase 4) et le tableau de bord (phase 5).
    Renvoie : ca (XAF), cout (XAF), marge (XAF), nb_prestations, top_service (nom ou None).
    """
    prestations = Prestation.objects.filter(
        secretariat=secretariat, statut=StatutPrestation.VALIDEE,
        cree_le__gte=debut, cree_le__lt=fin,
    )
    totaux = prestations.aggregate(ca=Sum("montant_total"), nb=Count("id"))
    lignes = LignePrestation.objects.filter(prestation__in=prestations)
    cout = lignes.aggregate(
        total=Sum(F("cout_unitaire") * F("quantite")),
    )["total"] or 0
    top = (
        lignes.values("nom_service")
        .annotate(total=Sum(F("prix_unitaire") * F("quantite")))
        .order_by("-total")
        .first()
    )
    ca = totaux["ca"] or 0
    return {
        "ca": ca,
        "cout": int(cout),
        "marge": ca - int(cout),
        "nb_prestations": totaux["nb"] or 0,
        "top_service": top["nom_service"] if top else None,
    }
