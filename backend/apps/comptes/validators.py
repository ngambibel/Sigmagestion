"""Validateurs propres au domaine des comptes."""
import re

from django.core.exceptions import ValidationError

# Numéro mobile camerounais : 9 chiffres commençant par 6, préfixe +237 optionnel.
_MOTIF_TELEPHONE = re.compile(r"^\+237[62]\d{8}$")


def normaliser_telephone(valeur: str) -> str:
    """Retire les espaces et normalise au format +237XXXXXXXXX.

    Accepte les saisies « +237 6XX XXX XXX », « 237 6XXXXXXXX », « 6XXXXXXXX ».
    Lève ValidationError si le numéro n'est pas un mobile camerounais valide.
    """
    if not valeur:
        raise ValidationError("Le numéro de téléphone est obligatoire.")
    compact = re.sub(r"[\s.-]", "", valeur)
    if compact.startswith("00237"):
        compact = "+" + compact[2:]
    elif compact.startswith("237"):
        compact = "+" + compact
    elif not compact.startswith("+"):
        compact = "+237" + compact
    if not _MOTIF_TELEPHONE.match(compact):
        raise ValidationError(
            "Numéro de téléphone camerounais invalide. "
            "Format attendu : +237 6XX XXX XXX."
        )
    return compact
