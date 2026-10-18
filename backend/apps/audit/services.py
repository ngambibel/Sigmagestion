"""Helper d'enregistrement du journal d'audit (RG-16)."""


def adresse_ip(request):
    if request is None:
        return None
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def tracer(
    *, action, instance=None, auteur=None, secretariat=None,
    avant=None, apres=None, request=None, objet_repr="",
):
    """Enregistre une opération sensible. Ne lève jamais : l'audit ne doit pas
    casser l'opération métier."""
    from .models import JournalAudit

    try:
        if secretariat is None and instance is not None:
            secretariat = getattr(instance, "secretariat", None)
        JournalAudit.objects.create(
            secretariat=secretariat,
            auteur=auteur if (auteur and getattr(auteur, "is_authenticated", False)) else None,
            action=action,
            modele=instance.__class__.__name__ if instance is not None else "",
            objet_id=str(getattr(instance, "pk", "") or ""),
            objet_repr=(objet_repr or str(instance))[:200] if instance is not None else objet_repr,
            valeurs_avant=avant,
            valeurs_apres=apres,
            ip=adresse_ip(request),
        )
    except Exception:  # noqa: BLE001 — l'audit est best-effort
        pass
