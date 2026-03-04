from django import forms
from .models import Electeur, Candidat


class ElecteurForm(forms.ModelForm):
    class Meta:
        model = Electeur
        fields = ['nom', 'prenom', 'region','sexe', 'telephon', 'numero_cni', 'date_naissance']
        widgets = {
            'date_naissance': forms.DateInput(attrs={'type': 'date'}),
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