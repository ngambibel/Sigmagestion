"""Administration Django pour les utilisateurs."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Utilisateur


@admin.register(Utilisateur)
class UtilisateurAdmin(BaseUserAdmin):
    ordering = ("telephone",)
    list_display = ("telephone", "nom", "role", "is_active", "doit_changer_mdp")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("telephone", "nom", "email")

    fieldsets = (
        (None, {"fields": ("telephone", "password")}),
        ("Identité", {"fields": ("nom", "email", "role")}),
        ("Sécurité", {"fields": ("doit_changer_mdp", "code_pin_hash")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser",
                                     "groups", "user_permissions")}),
        ("Dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("telephone", "nom", "role", "password1", "password2"),
        }),
    )
