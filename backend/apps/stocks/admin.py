from django.contrib import admin

from .models import Consommable, MouvementStock


@admin.register(Consommable)
class ConsommableAdmin(admin.ModelAdmin):
    list_display = ("nom", "secretariat", "qte_stock", "unite_mesure", "seuil_alerte", "actif")
    list_filter = ("actif",)
    search_fields = ("nom",)  # requis par l'autocomplete de la nomenclature


@admin.register(MouvementStock)
class MouvementStockAdmin(admin.ModelAdmin):
    list_display = ("cree_le", "consommable", "type", "quantite", "stock_apres", "auteur")
    list_filter = ("type",)
    search_fields = ("consommable__nom", "motif")
    readonly_fields = [f.name for f in MouvementStock._meta.fields]
