from django.db import models
import uuid

class Electeur(models.Model):

    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=150)
    numero_cni = models.CharField(max_length=20, unique=True)
    date_naissance = models.DateField()
    telephon = models.CharField(max_length=20, unique=True)

    sexe = models.CharField(max_length=10, choices=[('M', 'Masculin'), ('F', 'Féminin')], null=True)
    region = models.CharField(max_length=100, null=True)
    

    numero_electeur = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        blank=True,
        null=True
    )

    # ✅ AJOUTER CE CHAMP
    empreinte_hash = models.CharField(
        max_length=256,
        blank=True,
        null=True
    )

    date_inscription = models.DateTimeField(auto_now_add=True)


class Candidat(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    parti_politique = models.CharField(max_length=100)
    date_naissance = models.DateField()
    cautionnement_valide = models.BooleanField(default=False, verbose_name="Caution de 50M payée")
    photo = models.ImageField(upload_to='photos_candidats/')
    extrait_naissance = models.FileField(upload_to='documents_candidats/')
    casier_judiciaire = models.FileField(upload_to='documents_candidats/')

    class Meta:
        db_table = 'candidats'

    def __str__(self):
        return f"{self.nom} {self.prenom} ({self.parti_politique})"
    

    from django.db import models
from django.db.models import Count

class Resultat(models.Model):
    candidat = models.OneToOneField(
        'Candidat', 
        on_delete=models.CASCADE, 
        related_name='resultat'
    )
    nombre_votes = models.IntegerField(default=0)
    pourcentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    rang = models.IntegerField(default=0)
    date_calcul = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['rang']
        verbose_name = "Résultat"
        verbose_name_plural = "Résultats"

    def __str__(self):
        return f"{self.candidat.nom} - {self.nombre_votes} votes ({self.pourcentage}%)"

    @staticmethod
    def calculer():
        """ Recalcule et sauvegarde tous les résultats """
        from vote.models import Vote
        
        total_votes = Vote.objects.count()
        candidats = Candidat.objects.annotate(total=Count('votes_recus'))
        
        # Trier par votes décroissant pour attribuer les rangs
        candidats_tries = sorted(candidats, key=lambda c: c.total, reverse=True)
        
        for rang, candidat in enumerate(candidats_tries, start=1):
            pourcentage = (candidat.total / total_votes * 100) if total_votes > 0 else 0
            
            Resultat.objects.update_or_create(
                candidat=candidat,
                defaults={
                    'nombre_votes': candidat.total,
                    'pourcentage': round(pourcentage, 2),
                    'rang': rang,
                }
            )

