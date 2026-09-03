from django.contrib import admin

from .models import AbonnementPush


@admin.register(AbonnementPush)
class AbonnementPushAdmin(admin.ModelAdmin):
    list_display = ("utilisateur", "navigateur", "cree_le")
    search_fields = ("utilisateur__nom", "endpoint")
