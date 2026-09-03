"""Tâches Celery des notifications push."""
import json
import logging

from celery import shared_task
from django.conf import settings
from pywebpush import WebPushException, webpush

logger = logging.getLogger(__name__)


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
