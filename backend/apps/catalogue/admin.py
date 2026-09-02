from django.contrib import admin

from .models import NomenclatureService, Service


class NomenclatureInline(admin.TabularInline):
    model = NomenclatureService
    extra = 0
    autocomplete_fields = ("consommable",)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("nom", "secretariat", "prix", "unite_facturation", "consomme_stock", "actif")
    list_filter = ("consomme_stock", "actif", "categorie")
    search_fields = ("nom",)
    inlines = [NomenclatureInline]
