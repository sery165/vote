# vote/admin.py — FICHIER COMPLET FINAL

from django.contrib import admin
from .models import ParticipationVote, BulletinVote


@admin.register(ParticipationVote)
class ParticipationVoteAdmin(admin.ModelAdmin):
    list_display    = ('electeur', 'date_vote')
    search_fields   = ('electeur__nom',)
    readonly_fields = ('electeur', 'date_vote', 'jeton_utilise')


@admin.register(BulletinVote)
class BulletinVoteAdmin(admin.ModelAdmin):
    list_display    = ('candidat', 'date_vote')
    search_fields   = ('candidat__nom',)
    readonly_fields = ('candidat', 'date_vote', 'jeton_hash')