from django import forms
from .models import Electeur, Candidat


class ElecteurForm(forms.ModelForm):
    class Meta:
        model  = Electeur
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
            'sexe': forms.Select(choices=[
                ('', '-- Sélectionner --'),
                ('M', 'Masculin'),
                ('F', 'Féminin')
            ]),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.setdefault('class', 'form-control')

    def add_error(self, field, error):
        super().add_error(field, error)
        if field and field in self.fields:
            existing = self.fields[field].widget.attrs.get('class', '')
            if 'field-error' not in existing:
                self.fields[field].widget.attrs['class'] = existing + ' field-error'

    def clean_telephon(self):
        telephon = self.cleaned_data.get('telephon')
        if Electeur.objects.filter(telephon=telephon).exists():
            raise forms.ValidationError("⚠️ Ce numéro de téléphone est déjà utilisé.")
        return telephon

    def clean_numero_cni(self):
        numero_cni = self.cleaned_data.get('numero_cni')
        if Electeur.objects.filter(numero_cni=numero_cni).exists():
            raise forms.ValidationError("⚠️ Cette CNI / ce passeport est déjà enregistré(e).")
        return numero_cni


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