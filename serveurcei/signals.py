from django.db.models.signals import pre_save
from django.dispatch import receiver
import random
import string
from .models import Electeur

@receiver(pre_save, sender=Electeur)
def generer_numero_vote(sender, instance, **kwargs):
    if not instance.numero_electeur:
        # Génère un code unique de 10 caractères alphanumériques
        instance.numero_electeur = ''.join(random.choices(
            string.ascii_uppercase + string.digits, k=10
        ))