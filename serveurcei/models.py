# serveurcei/models.py
import uuid
import random
import hashlib
from django.db import models
from django.db.models import Count


class Electeur(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=150)
    numero_cni = models.CharField(max_length=20, unique=True)
    date_naissance = models.DateField()
    telephon = models.CharField(max_length=20, unique=True)
    sexe = models.CharField(max_length=10, choices=[('M', 'Masculin'), ('F', 'Féminin')], null=True)
    region = models.CharField(max_length=100, null=True)
    numero_electeur = models.CharField(max_length=20, unique=True, editable=False, blank=True, null=True)
    empreinte_hash = models.CharField(max_length=256, blank=True, null=True)
    date_inscription = models.DateTimeField(auto_now_add=True)
    is_alive = models.BooleanField(default=True)  # ← AJOUTÉ

    def save(self, *args, **kwargs):
        if not self.numero_electeur:
            prefix = "CEI-25-"
            random_digits = str(random.randint(100000, 999999))
            new_num = prefix + random_digits
            while Electeur.objects.filter(numero_electeur=new_num).exists():
                random_digits = str(random.randint(100000, 999999))
                new_num = prefix + random_digits
            self.numero_electeur = new_num
        super().save(*args, **kwargs)

    # ── Propriétés utiles pour le template ──

    @property
    def nom_complet(self):
        return f"{self.nom} {self.prenom}"

    @property
    def telephone(self):
        """Alias pour compatibilité template (telephon → telephone)"""
        return self.telephon

    @property
    def numero_piece(self):
        """Alias pour compatibilité template"""
        return self.numero_cni

    @property
    def has_voted(self):
        return ParticipationVote.objects.filter(electeur=self).exists()

    def __str__(self):
        return f"{self.nom} {self.prenom} - {self.numero_electeur}"


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


class ParticipationVote(models.Model):
    electeur = models.OneToOneField(Electeur, on_delete=models.CASCADE, related_name='participation')
    date_vote = models.DateTimeField(auto_now_add=True)
    jeton_utilise = models.UUIDField(default=uuid.uuid4, unique=True)

    class Meta:
        db_table = 'participations_vote'

    def __str__(self):
        return f"Électeur #{self.electeur_id} a voté"


class BulletinVote(models.Model):
    candidat = models.ForeignKey(Candidat, on_delete=models.CASCADE, related_name='bulletinvote')
    date_vote = models.DateTimeField(auto_now_add=True)
    jeton_hash = models.CharField(max_length=64, unique=True)

    class Meta:
        db_table = 'bulletins_vote'

    def __str__(self):
        return f"Vote anonyme pour {self.candidat}"


class AdminCEI(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    username = models.CharField(max_length=50, unique=True)
    password_hash = models.CharField(max_length=255)
    email = models.EmailField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Administrateur CEI"
        verbose_name_plural = "Administrateurs CEI"

    def __str__(self):
        return f"{self.username}"


class ActionLog(models.Model):
    admin = models.ForeignKey(AdminCEI, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.timestamp}] {self.action}"


class ElectionConfig(models.Model):
    nom_election = models.CharField(max_length=200, default="Élection Présidentielle")
    date_debut_vote = models.DateTimeField(null=True, blank=True)
    date_fin_vote = models.DateTimeField(null=True, blank=True)
    vote_actif = models.BooleanField(default=False)
    inscription_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Configuration élection"

    def __str__(self):
        return self.nom_election


class Resultat(models.Model):
    candidat = models.OneToOneField(Candidat, on_delete=models.CASCADE, related_name='resultat')
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