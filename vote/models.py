# models.py

import uuid
import hashlib
from django.db import models
from serveurcei.models import Electeur, Candidat


class ParticipationVote(models.Model):
    """
    Table 1 : Sait QUI a voté — mais PAS pour qui
    """
    electeur  = models.OneToOneField(
        Electeur,
        on_delete=models.CASCADE,
        related_name='participation'
    )
    date_vote    = models.DateTimeField(auto_now_add=True)
    jeton_utilise = models.UUIDField(default=uuid.uuid4, unique=True)

    class Meta:
        db_table = 'participations_vote'

    def __str__(self):
        return f"Électeur #{self.electeur_id} a voté"  # ← pas de candidat ici !


class BulletinVote(models.Model):
    """
    Table 2 : Sait POUR QUI — mais PAS qui a voté
    """
    candidat  = models.ForeignKey(
        Candidat,
        on_delete=models.CASCADE,
        related_name='votes_recus'
    )
    date_vote  = models.DateTimeField(auto_now_add=True)
    jeton_hash = models.CharField(max_length=64, unique=True)  # hash irréversible

    class Meta:
        db_table = 'bulletins_vote'

    def __str__(self):
        return f"Vote anonyme pour {self.candidat}"  # ← pas d'électeur ici !