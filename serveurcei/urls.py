from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'serveurcei'

router = DefaultRouter()
router.register(r'electeurs', views.ElecteurViewSet, basename='electeur')

urlpatterns = [
    # ── Accueil ──
    path('accueil-administration/', views.ancien_accueil, name='ancien_accueil'),

    # ── Inscriptions ──
    path('inscription-electeur/', views.inscription_electeur, name='inscription_electeur'),
    path('inscription-candidat/', views.inscription_candidat, name='inscription_candidat'),

    path('felicitations/', views.felicitations, name='felicitations'),

    # ── API Électeurs ──
    path('verif/<str:numero_cni>/', views.verif_electeur, name='verif_electeur'),
    path('attribuer-numero/<str:numero_cni>/', views.attribuer_numero, name='attribuer_numero'),

    # ── Empreintes ──
    path('verifier-empreinte/', views.verifier_empreinte, name='verifier_empreinte'),
    path('enregistrer-empreinte/', views.enregistrer_empreinte, name='enregistrer_empreinte'),

    # ── Vote ──
    path('vote/', views.page_vote, name='page_vote'),
    path('vote/soumettre/', views.voter, name='voter'),
    path('vote/succes/', views.vote_succes, name='vote_succes'),

    # ── Résultats & Stats ──
    path('resultats/', views.resultats, name='resultats'),
    path('votants/', views.votants, name='votants'),
    path('statistiques/', views.statistiques, name='statistiques'),
    path('api-resultats/', views.api_resultats, name='api_resultats'),

    # ── Reçus PDF ──
    path('telecharger-recu/<int:electeur_id>/', views.telecharger_recu_cei, name='telecharger_recu'),
    path('telecharger-recu-candidat/<int:candidat_id>/', views.telecharger_recu_candidat, name='telecharger_recu_candidat'),

    # Admin CEI Back-office mot nom admin et mot de pass admin123
    path('admin-cei/login/', views.admin_login, name='admin_login'),
    path('admin-cei/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-cei/electeurs/', views.admin_electeurs, name='admin_electeurs'),
    path('admin-cei/electeurs/<int:electeur_id>/supprimer/', views.admin_supprimer_electeur, name='admin_supprimer_electeur'),
    path('admin-cei/electeurs/<int:electeur_id>/deces/', views.admin_toggle_deces, name='admin_toggle_deces'),
    path('admin-cei/resultats/', views.admin_resultats, name='admin_resultats'),
    path('admin-cei/statistiques/', views.admin_statistiques, name='admin_statistiques'),
    path('admin-cei/logs/', views.admin_logs, name='admin_logs'),
    path('admin-cei/election/', views.admin_election, name='admin_election'),
    path('admin-cei/candidats/', views.admin_candidats, name='admin_candidats'),
    path('admin-cei/candidats/<int:candidat_id>/toggle/', views.admin_toggle_candidat, name='admin_toggle_candidat'),
    path('admin-cei/deconnexion/', views.admin_deconnexion, name='admin_deconnexion'),





    # ── API REST ──
    path('api/', include(router.urls)),
]