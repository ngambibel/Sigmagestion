"""Tâches Celery des notifications push."""
import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal

from celery import shared_task
from django.conf import settings
from django.db.models import Sum
from django.utils import timezone
from pywebpush import WebPushException, webpush

logger = logging.getLogger(__name__)


def _format_qte(valeur: Decimal) -> str:
    """Affiche 100 plutôt que 100.00."""
    return str(int(valeur)) if valeur == valeur.to_integral_value() else str(valeur)


def _xaf(montant: int) -> str:
    """Formate un entier XAF avec séparateur d'espace fine : 47500 → « 47 500 »."""
    return f"{int(montant):,}".replace(",", " ")


def _variation(courant: int, reference: int) -> str:
    """Flèche de comparaison avec la veille (↑/↓ en %), ou chaîne vide si non pertinent."""
    if reference <= 0:
        return ""
    pct = round((courant - reference) / reference * 100)
    if pct == 0:
        return " (= hier)"
    fleche = "↑" if pct > 0 else "↓"
    return f" {fleche} {abs(pct)}% vs hier"


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


def _type_actif(parametre, type) -> bool:
    """Indique si l'utilisateur a laissé ce type de notification activé (M6.6)."""
    from .models import TypeNotification

    bascules = {
        TypeNotification.STOCK_FAIBLE: parametre.alerte_stock_on,
        TypeNotification.BILAN_CA: parametre.alerte_ca_on,
        TypeNotification.ECART_CAISSE: parametre.alerte_ecart_caisse_on,
        TypeNotification.ANNULATION: parametre.alerte_annulation_on,
        TypeNotification.SESSION: parametre.alerte_session_on,
    }
    return bascules.get(type, True)


def notifier_utilisateur(utilisateur, secretariat, *, type, titre, corps, url="/", forcer=False):
    """Persiste une notification (centre M6.5) et l'envoie en push selon les réglages.

    - Si le type est désactivé (M6.6), on n'enregistre rien et on n'envoie rien.
    - Si « Ne pas déranger » est actif, la notification est enregistrée dans le centre
      mais aucun push n'est émis (une push manquée se rattrape dans l'app).
    - `forcer=True` (ex. notification de test) court-circuite ces réglages.
    """
    from apps.secretariats.models import ParametreNotification

    from .models import AbonnementPush, Notification

    parametre, _ = ParametreNotification.objects.get_or_create(secretariat=secretariat)
    if not forcer and not _type_actif(parametre, type):
        return

    Notification.objects.create(
        secretariat=secretariat, utilisateur=utilisateur,
        type=type, titre=titre, corps=corps, url=url,
    )
    if not forcer and parametre.ne_pas_deranger:
        return  # mode silencieux : pas de push

    for abonnement in AbonnementPush.objects.filter(utilisateur=utilisateur):
        envoyer_notification_push.delay(abonnement.id, titre, corps, url)


def notifier_annulation(prestation, auteur=None):
    """Prévient le propriétaire qu'une prestation a été annulée (M6.4)."""
    from .models import TypeNotification

    par_qui = f" par {auteur.nom}" if auteur else ""
    notifier_utilisateur(
        prestation.secretariat.proprietaire, prestation.secretariat,
        type=TypeNotification.ANNULATION,
        titre="Prestation annulée",
        corps=(
            f"Ticket {prestation.numero} ({_xaf(prestation.montant_total)} F) annulé{par_qui} : "
            f"{prestation.motif_annulation}"
        ),
        url="/ventes",
    )


def notifier_ecart_caisse(session):
    """Prévient le propriétaire d'un écart de caisse au-delà du seuil configuré (M6.4)."""
    from apps.secretariats.models import ParametreNotification

    from .models import TypeNotification

    if not session.ecart:
        return
    parametre, _ = ParametreNotification.objects.get_or_create(secretariat=session.secretariat)
    if abs(session.ecart) < parametre.seuil_ecart_caisse:
        return  # écart sous le seuil toléré
    nature = "manquant" if session.ecart < 0 else "excédent"
    notifier_utilisateur(
        session.secretariat.proprietaire, session.secretariat,
        type=TypeNotification.ECART_CAISSE,
        titre="Écart de caisse",
        corps=(
            f"Session de {session.employe.nom} clôturée : écart de "
            f"{_xaf(abs(session.ecart))} F ({nature})."
        ),
        url="/bilan",
    )


def notifier_session(session, *, ouverture: bool):
    """Prévient le propriétaire de l'ouverture / clôture d'une session (M6.4, option)."""
    from .models import TypeNotification

    if ouverture:
        titre = "Session ouverte"
        corps = f"{session.employe.nom} a ouvert une session (fond {_xaf(session.fond_initial)} F)."
    else:
        titre = "Session clôturée"
        corps = f"{session.employe.nom} a clôturé sa session de caisse."
    notifier_utilisateur(
        session.secretariat.proprietaire, session.secretariat,
        type=TypeNotification.SESSION, titre=titre, corps=corps, url="/bilan",
    )


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


def _plage_du_jour(secretariat, maintenant):
    """Renvoie la PlageHoraire du jour courant (créée au besoin)."""
    from apps.secretariats.models import plages_par_defaut

    jour = maintenant.weekday()
    plage = secretariat.plages_horaires.filter(jour=jour).first()
    if plage is None:
        plages_par_defaut(secretariat)
        plage = secretariat.plages_horaires.filter(jour=jour).first()
    return plage


def _debut_jour(maintenant):
    """Minuit local du jour de `maintenant` (datetime tz-aware)."""
    return maintenant.replace(hour=0, minute=0, second=0, microsecond=0)


def _instant_local(date_locale, heure):
    """Compose un datetime tz-aware à partir d'une date et d'une heure locales."""
    return timezone.make_aware(datetime.combine(date_locale, heure))


def traiter_bilan_ca(secretariat, parametre, maintenant) -> bool:
    """Envoie, si les conditions sont réunies, le bilan de CA d'un secrétariat.

    Conditions : bilan activé, instant dans la plage horaire du jour (RG-09),
    intervalle écoulé depuis le dernier envoi, et CA non entièrement nul (RG-10).
    Renvoie True si une notification a été émise.
    """
    from apps.ventes.services import agreger_ca

    from .models import TypeNotification

    if not parametre.alerte_ca_on:
        return False

    plage = _plage_du_jour(secretariat, maintenant)
    if plage is None or not plage.contient(maintenant.time()):
        return False  # RG-09 : hors plage ou jour fermé

    # Intervalle écoulé depuis le dernier envoi ?
    dernier = timezone.localtime(parametre.dernier_envoi_ca) if parametre.dernier_envoi_ca else None
    if dernier and (maintenant - dernier) < timedelta(minutes=parametre.intervalle_ca_min):
        return False

    ouverture = _instant_local(maintenant.date(), plage.heure_debut)
    # Début de l'intervalle = dernier envoi s'il date d'aujourd'hui après l'ouverture, sinon ouverture.
    debut_intervalle = dernier if (dernier and dernier >= ouverture) else ouverture

    agg_intervalle = agreger_ca(secretariat, debut_intervalle, maintenant)
    agg_jour = agreger_ca(secretariat, _debut_jour(maintenant), maintenant)

    if agg_intervalle["ca"] == 0 and agg_jour["ca"] == 0:
        return False  # RG-10 : jour creux, on ne dérange pas

    # Comparaison avec la même tranche la veille.
    ca_veille = agreger_ca(
        secretariat, debut_intervalle - timedelta(days=1), maintenant - timedelta(days=1),
    )["ca"]
    variation = _variation(agg_intervalle["ca"], ca_veille)

    titre = f"Bilan {maintenant:%Hh%M} — {secretariat.nom}"
    corps = (
        f"{_xaf(agg_intervalle['ca'])} F encaissés depuis {debut_intervalle:%Hh%M} · "
        f"{_xaf(agg_jour['ca'])} F aujourd'hui{variation}.\n"
        f"{agg_jour['nb_prestations']} prestations"
    )
    if agg_intervalle["top_service"]:
        corps += f" · {agg_intervalle['top_service']} en tête"

    notifier_utilisateur(
        secretariat.proprietaire, secretariat,
        type=TypeNotification.BILAN_CA, titre=titre, corps=corps, url="/bilan",
    )
    parametre.dernier_envoi_ca = maintenant
    parametre.save(update_fields=["dernier_envoi_ca"])
    return True


def traiter_bilan_jour(secretariat, parametre, maintenant) -> bool:
    """Envoie le récapitulatif complet de la journée à la fermeture (une fois par jour)."""
    from apps.caisse.models import Depense
    from apps.ventes.services import agreger_ca

    from .models import TypeNotification

    if not parametre.bilan_jour_on:
        return False
    if parametre.dernier_bilan_jour == maintenant.date():
        return False  # déjà envoyé aujourd'hui

    plage = _plage_du_jour(secretariat, maintenant)
    if plage is None or not plage.ouvert or maintenant.time() < plage.heure_fin:
        return False  # jour fermé, ou pas encore l'heure de fermeture

    debut = _debut_jour(maintenant)
    agg = agreger_ca(secretariat, debut, maintenant)
    # On marque le jour comme traité même sans vente, pour ne pas réessayer en boucle.
    parametre.dernier_bilan_jour = maintenant.date()
    parametre.save(update_fields=["dernier_bilan_jour"])
    if agg["nb_prestations"] == 0:
        return False  # jour creux : pas de notification

    depenses = (
        Depense.objects.filter(secretariat=secretariat, cree_le__gte=debut, cree_le__lt=maintenant)
        .aggregate(total=Sum("montant"))["total"]
        or 0
    )
    solde = agg["ca"] - depenses
    titre = f"Clôture — {secretariat.nom}"
    corps = (
        f"Journée terminée : {_xaf(agg['ca'])} F de CA, {agg['nb_prestations']} prestations.\n"
        f"Dépenses {_xaf(depenses)} F · solde {_xaf(solde)} F · marge estimée {_xaf(agg['marge'])} F."
    )
    notifier_utilisateur(
        secretariat.proprietaire, secretariat,
        type=TypeNotification.BILAN_CA, titre=titre, corps=corps, url="/bilan",
    )
    return True


def _secretariats_a_traiter():
    """Secrétariats dont l'installation est terminée, avec leurs paramètres de notification."""
    from apps.secretariats.models import ParametreNotification, Secretariat

    for secretariat in Secretariat.objects.filter(onboarding_termine=True).select_related(
        "proprietaire"
    ):
        parametre, _ = ParametreNotification.objects.get_or_create(secretariat=secretariat)
        yield secretariat, parametre


@shared_task(ignore_result=True)
def notifier_ca_periodique():
    """Balaie les secrétariats et envoie le bilan de CA aux moments voulus (toutes les 15 min)."""
    maintenant = timezone.localtime()
    envois = 0
    for secretariat, parametre in _secretariats_a_traiter():
        try:
            if traiter_bilan_ca(secretariat, parametre, maintenant):
                envois += 1
        except Exception:  # noqa: BLE001 — un secrétariat en erreur ne doit pas bloquer les autres
            logger.exception("Échec du bilan de CA pour le secrétariat %s", secretariat.id)
    return envois


@shared_task(ignore_result=True)
def bilan_fin_journee():
    """Envoie le récapitulatif de clôture à la fermeture de chaque secrétariat (toutes les 15 min)."""
    maintenant = timezone.localtime()
    envois = 0
    for secretariat, parametre in _secretariats_a_traiter():
        try:
            if traiter_bilan_jour(secretariat, parametre, maintenant):
                envois += 1
        except Exception:  # noqa: BLE001
            logger.exception("Échec du bilan de journée pour le secrétariat %s", secretariat.id)
    return envois
