from django.contrib import admin

from .models import LignePrestation, Prestation


class LignePrestationInline(admin.TabularInline):
    model = LignePrestation
    extra = 0
    readonly_fields = ("service", "nom_service", "prix_unitaire", "quantite", "cout_unitaire")


@admin.register(Prestation)
class PrestationAdmin(admin.ModelAdmin):
    list_display = ("numero", "secretariat", "montant_total", "mode_paiement", "statut", "employe", "cree_le")
    list_filter = ("statut", "mode_paiement")
    search_fields = ("numero",)
    inlines = [LignePrestationInline]
    readonly_fields = ("numero", "cree_le")
