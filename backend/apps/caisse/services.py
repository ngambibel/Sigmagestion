"""Logique métier de la caisse : clôture et calcul de l'écart (RG-12)."""
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from .models import Depense, SessionCaisse, StatutSession


class CaisseError(Exception):
    """Erreur métier de caisse (renvoyée en 400)."""


def montant_theorique_session(session: SessionCaisse) -> int:
    """Espèces attendues en caisse : fond + ventes espèces validées − dépenses.

    Les ventes non espèces (MoMo, Orange, crédit) n'alimentent pas le tiroir.
    Les prestations annulées sont exclues.
    """
    from apps.ventes.models import ModePaiement, Prestation, StatutPrestation

    ventes_especes = (
        Prestation.objects.filter(
            session=session,
            statut=StatutPrestation.VALIDEE,
            mode_paiement=ModePaiement.ESPECES,
        ).aggregate(total=Sum("montant_total"))["total"]
        or 0
    )
    depenses = (
        Depense.objects.filter(session=session).aggregate(total=Sum("montant"))["total"] or 0
    )
    return session.fond_initial + ventes_especes - depenses


def cout_consommables_session(session: SessionCaisse) -> int:
    """Coût de revient des consommables utilisés par les ventes validées de la session.

    Somme de (coût unitaire figé × quantité) sur toutes les lignes des prestations
    validées. Les prestations annulées sont exclues (leur stock a été réinjecté).
    """
    from django.db.models import F

    from apps.ventes.models import LignePrestation, StatutPrestation

    total = (
        LignePrestation.objects.filter(
            prestation__session=session,
            prestation__statut=StatutPrestation.VALIDEE,
        ).aggregate(total=Sum(F("cout_unitaire") * F("quantite")))["total"]
        or 0
    )
    return int(total)


def chiffre_affaires_session(session: SessionCaisse) -> int:
    """Chiffre d'affaires des ventes validées de la session, tous modes de paiement."""
    from apps.ventes.models import Prestation, StatutPrestation

    return (
        Prestation.objects.filter(session=session, statut=StatutPrestation.VALIDEE).aggregate(
            total=Sum("montant_total")
        )["total"]
        or 0
    )


@transaction.atomic
def cloturer_session(session: SessionCaisse, *, montant_compte: int, commentaire: str = "") -> SessionCaisse:
    session = SessionCaisse.objects.select_for_update().get(pk=session.pk)
    if session.statut != StatutSession.OUVERTE:
        raise CaisseError("Cette session est déjà clôturée.")

    theorique = montant_theorique_session(session)
    ecart = int(montant_compte) - theorique

    # RG-12 : un écart non nul impose un commentaire.
    commentaire = (commentaire or "").strip()
    if ecart != 0 and not commentaire:
        raise CaisseError("Un écart a été constaté : un commentaire est obligatoire.")

    session.montant_theorique = theorique
    session.montant_compte = int(montant_compte)
    session.ecart = ecart
    session.commentaire = commentaire
    session.statut = StatutSession.CLOTUREE
    session.cloturee_le = timezone.now()
    session.save(
        update_fields=[
            "montant_theorique", "montant_compte", "ecart",
            "commentaire", "statut", "cloturee_le",
        ]
    )

    def _prevenir():
        from apps.notifications.tasks import notifier_ecart_caisse, notifier_session

        notifier_ecart_caisse(session)
        notifier_session(session, ouverture=False)

    transaction.on_commit(_prevenir)
    return session
