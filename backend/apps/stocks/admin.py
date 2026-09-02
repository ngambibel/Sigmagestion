from django.contrib import admin

from .models import Consommable


@admin.register(Consommable)
class ConsommableAdmin(admin.ModelAdmin):
    list_display = ("nom", "secretariat", "qte_stock", "unite_mesure", "seuil_alerte", "actif")
    list_filter = ("actif",)
    search_fields = ("nom",)
