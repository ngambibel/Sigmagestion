from django.contrib import admin

from .models import AbonnementPush, Notification


@admin.register(AbonnementPush)
class AbonnementPushAdmin(admin.ModelAdmin):
    list_display = ("utilisateur", "navigateur", "cree_le")
    search_fields = ("utilisateur__nom", "endpoint")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("titre", "utilisateur", "type", "lu", "archivee", "cree_le")
    list_filter = ("type", "lu", "archivee")
    search_fields = ("titre", "corps")
