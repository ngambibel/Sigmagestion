"""Déclencheurs des notifications."""
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.stocks.models import MouvementStock

from .tasks import verifier_seuils_stock


@receiver(post_save, sender=MouvementStock)
def declencher_verification_seuil(sender, instance, created, **kwargs):
    """Après chaque mouvement de stock (une fois la transaction validée),
    on demande à Celery d'évaluer le seuil du consommable concerné."""
    if not created:
        return
    consommable_id = instance.consommable_id
    transaction.on_commit(lambda: verifier_seuils_stock.delay(consommable_id))
