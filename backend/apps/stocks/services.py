"""Logique métier des stocks (isolée des vues, réutilisable et testable).

RG-07 : à chaque entrée de stock, le prix d'achat unitaire du consommable est
recalculé en **coût unitaire moyen pondéré (CUMP)**.
"""
from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction

from .models import Consommable, MouvementStock, TypeMouvement


def _entier(valeur: Decimal) -> int:
    """Arrondit un Decimal à l'entier XAF le plus proche."""
    return int(valeur.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


@transaction.atomic
def enregistrer_entree_stock(
    *,
    consommable: Consommable,
    quantite: Decimal,
    prix_total_lot: int,
    auteur=None,
    fournisseur: str = "",
    motif: str = "",
) -> MouvementStock:
    """Enregistre un réapprovisionnement, met à jour le stock et le CUMP.

    `prix_total_lot` est le prix d'achat total du lot entrant (XAF). Le prix
    unitaire entrant en découle, puis le CUMP est pondéré par les quantités.
    """
    quantite = Decimal(quantite)
    if quantite <= 0:
        raise ValueError("La quantité entrante doit être strictement positive.")

    # Verrou de ligne : évite les courses sur qte_stock / prix_achat.
    consommable = Consommable.objects.select_for_update().get(pk=consommable.pk)

    stock_avant = consommable.qte_stock
    stock_apres = stock_avant + quantite

    prix_unitaire_entrant = _entier(Decimal(prix_total_lot) / quantite)

    # CUMP = (valeur du stock existant + valeur du lot entrant) / quantité totale
    valeur_existante = stock_avant * Decimal(consommable.prix_achat)
    valeur_entrante = quantite * Decimal(prix_unitaire_entrant)
    cump = _entier((valeur_existante + valeur_entrante) / stock_apres)

    consommable.qte_stock = stock_apres
    consommable.prix_achat = cump
    if fournisseur:
        consommable.fournisseur = fournisseur
    consommable.save(update_fields=["qte_stock", "prix_achat", "fournisseur", "modifie_le"])

    return MouvementStock.objects.create(
        secretariat=consommable.secretariat,
        consommable=consommable,
        type=TypeMouvement.ENTREE,
        quantite=quantite,
        stock_avant=stock_avant,
        stock_apres=stock_apres,
        prix_achat_unitaire=prix_unitaire_entrant,
        motif=motif,
        auteur=auteur,
    )
