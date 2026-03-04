from django.db import models
from serveurcei.models import Electeur, Candidat  # ← import direct

class Vote(models.Model):
    electeur  = models.OneToOneField(
        Electeur,
        on_delete=models.CASCADE,
        related_name='vote_effectue'
    )
    candidat  = models.ForeignKey(
        Candidat,
        on_delete=models.CASCADE,
        related_name='votes_recus'
    )
    date_vote = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'votes'

    def __str__(self):
        return f"{self.electeur} → {self.candidat}"