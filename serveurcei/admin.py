from django.contrib import admin
from .models import Candidat, Electeur, Resultat, ParticipationVote


# ───── ELECTEUR ─────
@admin.register(Electeur)
class ElecteurAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prenom', 'numero_cni', 'numero_electeur', 'date_inscription', 'a_vote')
    readonly_fields = ('numero_electeur',)

    def a_vote(self, obj):
        return hasattr(obj, 'participation')
    a_vote.boolean = True
    a_vote.short_description = "A voté"


# ───── CANDIDAT ─────
@admin.register(Candidat)
class CandidatAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prenom', 'parti_politique', 'cautionnement_valide')


# ───── RESULTAT ─────
@admin.register(Resultat)
class ResultatAdmin(admin.ModelAdmin):
    list_display = ('rang', 'candidat', 'nombre_votes', 'pourcentage', 'date_calcul')
    ordering = ['rang']
    readonly_fields = ('rang', 'nombre_votes', 'pourcentage', 'date_calcul')


# ───── PARTICIPATION ─────
@admin.register(ParticipationVote)
class ParticipationVoteAdmin(admin.ModelAdmin):
    list_display = ('electeur', 'date_vote', 'jeton_utilise')
    search_fields = ('electeur__nom', 'electeur__prenom', 'electeur__numero_electeur')
    list_filter = ('date_vote',)