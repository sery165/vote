# vote/admin.py

from django.contrib import admin
from .models import Vote

# Vote est déjà enregistré via VoteAdmin, donc on ne fait rien ici
# Si vous voulez personnaliser, utilisez cette approche :

@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display  = ['electeur', 'candidat', 'date_vote']
    list_filter   = ['candidat']
    search_fields = ['electeur__nom', 'electeur__numero_electeur']