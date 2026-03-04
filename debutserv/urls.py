# ============================================================
#  FICHIER : monprojet/urls.py  (fichier URLs RACINE du projet)
# ============================================================

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from serveurcei import views as cei_views

# ── Router API REST ──
router = DefaultRouter()
router.register(r'electeurs', cei_views.ElecteurViewSet)

urlpatterns = [

    # ────────────────────────────────────────
    # 1) ADMIN DJANGO
    # ────────────────────────────────────────
    path('admin/', admin.site.urls),

    # ────────────────────────────────────────
    # 2) PAGES SERVEURCEI (accueil CEI, stats)
    # ────────────────────────────────────────
    path('', cei_views.accueil3, name='accueil3'),
    
    path('votants/', cei_views.votants, name='votants'),
    path('statistiques/', cei_views.statistiques, name='statistiques'),
    path('api-resultats/', cei_views.api_resultats, name='api_resultats'),

    # ────────────────────────────────────────
    # 3) TOUTES LES URLS DE serveurcei
    #    (inscription électeur, candidat, etc.)
    # ────────────────────────────────────────
    path('cei/', include('serveurcei.urls')),

    # ────────────────────────────────────────
    # 4) TOUTES LES URLS DE vote
    #    (page de vote, soumission, succès)
    # ────────────────────────────────────────
    path('vote/', include('vote.urls')),

    # ────────────────────────────────────────
    # 5) API REST
    # ────────────────────────────────────────
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)