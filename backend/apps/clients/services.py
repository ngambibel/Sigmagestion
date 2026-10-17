"""Logique métier des créances : règlements et mise à jour de l'encours."""
from django.db import transaction


class ClientError(Exception):
    """Erreur métier liée aux clients/créances (renvoyée en 400)."""


@transaction.atomic
def enregistrer_reglement(*, client, montant, auteur=None, commentaire=""):
    """Enregistre un règlement (partiel ou total) et décrémente l'encours.

    Le montant ne peut pas dépasser l'encours dû. Verrou pessimiste sur le client
    pour éviter deux règlements concurrents qui passeraient l'encours en négatif.
    """
    from .models import Client, Reglement

    montant = int(montant)
    if montant <= 0:
        raise ClientError("Le montant du règlement doit être positif.")

    client = Client.objects.select_for_update().get(pk=client.pk)
    if montant > client.encours:
        raise ClientError(
            f"Le règlement ({montant} XAF) dépasse l'encours dû ({client.encours} XAF)."
        )

    reglement = Reglement.objects.create(
        secretariat=client.secretariat, client=client, montant=montant,
        auteur=auteur, commentaire=(commentaire or "").strip(),
    )
    client.encours -= montant
    client.save(update_fields=["encours"])
    return reglement, client
