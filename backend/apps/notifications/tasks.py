"""Tâches Celery des notifications push."""
import json
import logging
from datetime import timedelta
from decimal import Decimal

from celery import shared_task
from django.conf import settings
from django.utils import timezone
from pywebpush import WebPushException, webpush

logger = logging.getLogger(__name__)


def _format_qte(valeur: Decimal) -> str:
    """Affiche 100 plutôt que 100.00."""
    return str(int(valeur)) if valeur == valeur.to_integral_value() else str(valeur)


@shared_task(ignore_result=True)
def envoyer_notification_push(abonnement_id: int, titre: str, corps: str, url: str = "/"):
    """Envoie une notification push à un abonnement.

    Supprime l'abonnement s'il est expiré/invalide (HTTP 404/410).
    """
    from .models import AbonnementPush

    abonnement = AbonnementPush.objects.filter(id=abonnement_id).first()
    if abonnement is None:
        return

    if not settings.VAPID_PUBLIC_KEY:
        logger.warning("VAPID non configuré : notification ignorée.")
        return

    try:
        webpush(
            subscription_info=abonnement.info_abonnement(),
            data=json.dumps({"titre": titre, "corps": corps, "url": url}),
            vapid_private_key=settings.VAPID_PRIVATE_KEY_PATH,
            vapid_claims={"sub": settings.VAPID_CLAIM_EMAIL},
        )
    except WebPushException as exc:
        statut = getattr(exc.response, "status_code", None)
        if statut in (404, 410):
            abonnement.delete()  # abonnement expiré : on le retire
            logger.info("Abonnement push %s expiré, supprimé.", abonnement_id)
        else:
            logger.error("Échec d'envoi push (%s) : %s", statut, exc)
            raise


def notifier_utilisateur(utilisateur, secretariat, *, type, titre, corps, url="/"):
    """Persiste une notification et l'envoie en push sur tous les appareils de l'utilisateur."""
    from .models import AbonnementPush, Notification

    Notification.objects.create(
        secretariat=secretariat, utilisateur=utilisateur,
        type=type, titre=titre, corps=corps, url=url,
    )
    for abonnement in AbonnementPush.objects.filter(utilisateur=utilisateur):
        envoyer_notification_push.delay(abonnement.id, titre, corps, url)


@shared_task(ignore_result=True)
def verifier_seuils_stock(consommable_id: int):
    """Après un mouvement, alerte le propriétaire si le stock passe sous le seuil.

    RG-08 : au plus une alerte par 24 h et par consommable tant que le stock reste bas.
    Le compteur se réarme automatiquement quand le stock repasse au-dessus du seuil.
    """
    from apps.stocks.models import Consommable
    from .models import TypeNotification

    consommable = (
        Consommable.objects.select_related("secretariat__proprietaire")
        .filter(id=consommable_id)
        .first()
    )
    if consommable is None or not consommable.actif:
        return

    if not consommable.sous_seuil:
        # Stock revenu au-dessus du seuil : on réarme l'alerte.
        if consommable.derniere_alerte_le is not None:
            consommable.derniere_alerte_le = None
            consommable.save(update_fields=["derniere_alerte_le"])
        return

    maintenant = timezone.now()
    if (
        consommable.derniere_alerte_le
        and maintenant - consommable.derniere_alerte_le < timedelta(hours=24)
    ):
        return  # déjà alerté récemment

    corps = (
        f"{consommable.nom} : il reste {_format_qte(consommable.qte_stock)} "
        f"{consommable.unite_mesure} sur un seuil de {_format_qte(consommable.seuil_alerte)}."
    )
    notifier_utilisateur(
        consommable.secretariat.proprietaire,
        consommable.secretariat,
        type=TypeNotification.STOCK_FAIBLE,
        titre="Stock faible",
        corps=corps,
        url="/stock",
    )
    consommable.derniere_alerte_le = maintenant
    consommable.save(update_fields=["derniere_alerte_le"])
