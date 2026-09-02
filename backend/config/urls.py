"""Routage racine de SigmaGestion."""
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("core.urls")),
    path("api/v1/", include("apps.comptes.urls")),
    path("api/v1/", include("apps.secretariats.urls")),
    path("api/v1/", include("apps.catalogue.urls")),
    path("api/v1/", include("apps.stocks.urls")),
    path("api/v1/", include("apps.caisse.urls")),
    # Documentation API
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]
