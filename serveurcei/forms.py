from django import forms
from .models import Electeur, Candidat

class ElecteurForm(forms.ModelForm):
    class Meta:
        model  = Electeur
        # ✅ Uniquement les champs qui existent dans le modèle
        fields = [
            'nom',
            'prenom',
            'numero_cni',
            'date_naissance',
            'telephon',
            'sexe',
            'region',
        ]
        widgets = {
            'date_naissance': forms.DateInput(attrs={'type': 'date'}),
            'sexe': forms.Select(choices=[('', '-- Sélectionner --'), ('M', 'Masculin'), ('F', 'Féminin')]),
        }

class CandidatForm(forms.ModelForm):
    class Meta:
        model = Candidat
        fields = [
            'nom', 'prenom', 'parti_politique', 'date_naissance',
            'cautionnement_valide', 'photo', 'extrait_naissance', 'casier_judiciaire'
        ]
        widgets = {
            'date_naissance': forms.DateInput(attrs={'type': 'date'}),
        }