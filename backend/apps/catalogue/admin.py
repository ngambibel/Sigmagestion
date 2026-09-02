from django.contrib import admin

from .models import Service


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("nom", "secretariat", "prix", "unite_facturation", "consomme_stock", "actif")
    list_filter = ("consomme_stock", "actif", "categorie")
    search_fields = ("nom",)
