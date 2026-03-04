from django.urls import path, include
from serveurcei.views import ElecteurViewSet, verif_electeur, attribuer_numero
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'electeurs', ElecteurViewSet, basename='electeur')

urlpatterns = [
    path('accueil-administration/', views.ancien_accueil, name='ancien_accueil'),
    path('verif/<str:numero_cni>/', verif_electeur, name='verif_electeur'),
    path('attribuer_numero/<str:numero_cni>/', attribuer_numero, name='attribuer_numero'),
    path('', include(router.urls)),
    path('inscription-electeur/', views.inscription_electeur, name='inscription_electeur'),
    path('inscription-candidat/', views.inscription_candidat, name='inscription_candidat'),
    path('resultats/', views.resultats, name='resultats'),  # ← views.resultats
]