from django.contrib import admin
from .models import Candidat, Electeur, Resultat  # ← ajoute Resultat

class ElecteurAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prenom', 'numero_cni', 'numero_electeur', 'date_inscription')
    readonly_fields = ('numero_electeur',)

# Ajoute ceci
@admin.register(Resultat)
class ResultatAdmin(admin.ModelAdmin):
    list_display = ('rang', 'candidat', 'nombre_votes', 'pourcentage', 'date_calcul')
    ordering = ['rang']
    readonly_fields = ('rang', 'nombre_votes', 'pourcentage', 'date_calcul')

admin.site.register(Candidat)
admin.site.register(Electeur, ElecteurAdmin)