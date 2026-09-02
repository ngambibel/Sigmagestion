"""Reconstruit `qte_stock` de chaque consommable à partir de ses mouvements.

Filet de sécurité (cahier §) : la quantité en stock est dénormalisée ; en cas de
doute, on la recalcule comme la somme signée des mouvements enregistrés.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db.models import Sum

from apps.stocks.models import Consommable


class Command(BaseCommand):
    help = "Recalcule qte_stock de chaque consommable à partir des mouvements."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Affiche les écarts sans rien modifier.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        corriges = 0
        for consommable in Consommable.objects.all():
            total = consommable.mouvements.aggregate(s=Sum("quantite"))["s"] or Decimal("0")
            if consommable.qte_stock != total:
                self.stdout.write(
                    f"{consommable.nom} (#{consommable.id}) : "
                    f"{consommable.qte_stock} → {total}"
                )
                if not dry_run:
                    consommable.qte_stock = total
                    consommable.save(update_fields=["qte_stock", "modifie_le"])
                corriges += 1
        verbe = "à corriger" if dry_run else "corrigé(s)"
        self.stdout.write(self.style.SUCCESS(f"{corriges} consommable(s) {verbe}."))
