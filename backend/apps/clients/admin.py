from django.contrib import admin

from .models import Client, Reglement


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("nom", "telephone", "type", "encours", "plafond_credit", "actif")
    list_filter = ("type", "actif")
    search_fields = ("nom", "telephone")


@admin.register(Reglement)
class ReglementAdmin(admin.ModelAdmin):
    list_display = ("client", "montant", "auteur", "cree_le")
    search_fields = ("client__nom",)
