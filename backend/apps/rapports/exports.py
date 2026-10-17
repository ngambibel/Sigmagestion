"""Exports des rapports : CSV (listes). Le PDF de synthèse est produit côté
navigateur (impression → « Enregistrer en PDF ») à partir des mêmes données JSON,
ce qui évite une dépendance serveur lourde et reste fidèle à la charte."""
import csv
import io

from django.http import HttpResponse


def rapport_en_csv(rapport: dict, nom_fichier: str) -> HttpResponse:
    """Sérialise un rapport {colonnes, lignes} en fichier CSV téléchargeable.

    Un seul BOM UTF-8 en tête (Excel FR ouvre alors correctement les accents) ;
    séparateur « ; » (convention francophone).
    """
    tampon = io.StringIO()
    colonnes = rapport["colonnes"]
    writer = csv.writer(tampon, delimiter=";")
    writer.writerow([c["libelle"] for c in colonnes])
    for ligne in rapport["lignes"]:
        writer.writerow([ligne.get(c["cle"], "") for c in colonnes])

    totaux = rapport.get("totaux", {})
    lignes_totaux = [(cle, val) for cle, val in totaux.items() if isinstance(val, (int, float))]
    if lignes_totaux:
        writer.writerow([])
        for cle, val in lignes_totaux:
            writer.writerow([cle.replace("_", " ").capitalize(), val])

    # Encodage avec un unique BOM, sans laisser Django ré-encoder en utf-8-sig.
    contenu = ("﻿" + tampon.getvalue()).encode("utf-8")
    reponse = HttpResponse(contenu, content_type="text/csv; charset=utf-8")
    reponse["Content-Disposition"] = f'attachment; filename="{nom_fichier}.csv"'
    return reponse
