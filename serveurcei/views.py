from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db.models import Count
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
import uuid
import random
import string

from .models import Electeur, Candidat
from vote.models import Vote          # ✅ Vote vient de l'app vote
from .forms import ElecteurForm, CandidatForm
from .serializers import ElecteurSerializer

# --- VUES PRINCIPALES ---

def accueil3(request):
    """ Page d'accueil principale avec statistiques """
    context = {
        'nb_electeurs' : Electeur.objects.count(),
        'nb_candidats' : Candidat.objects.filter(cautionnement_valide=True).count(),
        'nb_votes'     : Vote.objects.count(),
    }
    return render(request, 'accueil3.html', context)

def ancien_accueil(request): # Corrigé avec _
    return render(request, "ancien_accueil.html")

# --- INSCRIPTION ---

def inscription_electeur(request):
    if request.method == 'POST':
        if request.content_type != 'application/json':
            form = ElecteurForm(request.POST, request.FILES)
            if form.is_valid():
                electeur = form.save()
                print(f"✅ SUCCÈS : {electeur.nom} inscrit.")
                return render(request, 'confirmation_inscription.html', {'electeur': electeur})
            else:
                return render(request, 'inscription_electeur.html', {'form': form, 'errors': form.errors})
        else:
            data = request.data
            try:
                electeur = Electeur.objects.create(
                    nom=data.get('nom'),
                    prenom=data.get('prenom'),
                    numero_cni=data.get('numero_cni'),
                    date_naissance=data.get('date_naissance'),
                    telephon=data.get('telephon')
                )
                return Response({"message": "Inscrit", "numero": electeur.numero_electeur}, status=201)
            except Exception as e:
                return Response({"error": str(e)}, status=400)

    form = ElecteurForm()
    return render(request, 'inscription_electeur.html', {'form': form})

# --- LOGIQUE ÉLECTORALE ---

@api_view(['POST'])
def attribuer_numero(request, numero_cni):
    try:
        electeur = Electeur.objects.get(numero_cni=numero_cni)
        return Response({"numero_electeur": electeur.numero_electeur})
    except Electeur.DoesNotExist:
        return Response({"error": "Electeur non trouvé"}, status=404)

@api_view(['GET'])
def verif_electeur(request, numero_cni):
    try:
        electeur = Electeur.objects.get(numero_cni=numero_cni)
        return Response({"status": "trouvé", "numero": electeur.numero_electeur})
    except Electeur.DoesNotExist:
        return Response({"status": "inconnu"}, status=404)

def votants(request):
    votes = Vote.objects.all()
    return render(request, "votants.html", {"votes": votes})

def statistiques(request):
    return render(request, "statistiques.html")

def api_resultats(request):
    candidats = Candidat.objects.annotate(total=Count('votes_recus'))
    total_votes = Vote.objects.count()
    data = []
    for c in candidats:
        pourcentage = (c.total / total_votes * 100) if total_votes > 0 else 0
        data.append({"nom": c.nom, "pourcentage": round(pourcentage, 2)})
    return JsonResponse(data, safe=False)

# --- VIEWSET API ---
class ElecteurViewSet(viewsets.ModelViewSet):
    queryset = Electeur.objects.all()
    serializer_class = ElecteurSerializer


    # Ajoute ceci à la fin de ton fichier serveurcei/views.py
def inscription_candidat(request):
    if request.method == 'POST':
        form = CandidatForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return render(request, 'succes_candidat.html')
    else:
        form = CandidatForm()
    return render(request, 'inscription_candidat.html', {'form': form})

def ancien_accueil(request):
    # On initialise les formulaires vides pour l'affichage initial
    form_electeur = ElecteurForm()
    form_candidat = CandidatForm()

    if request.method == 'POST':
        form_type = request.POST.get('form_type') # On identifie quel formulaire est soumis

        if form_type == 'electeur':
            form_electeur = ElecteurForm(request.POST, request.FILES)
            if form_electeur.is_valid():
                electeur = form_electeur.save()
                print(f"✅ SUCCÈS : Électeur {electeur.nom} enregistré en base !")
                # Tu peux ajouter un message de succès ici
                context = {'nb_electeurs': Electeur.objects.count(), 'nb_candidats': Candidat.objects.count()}
                return render(request, "ancien_accueil.html", context)
            else:
                print(f"❌ ERREUR Électeur : {form_electeur.errors}")

        elif form_type == 'candidat':
            form_candidat = CandidatForm(request.POST, request.FILES)
            if form_candidat.is_valid():
                form_candidat.save()
                print("✅ SUCCÈS : Candidat enregistré !")
                context = {'nb_electeurs': Electeur.objects.count(), 'nb_candidats': Candidat.objects.count()}
                return render(request, "ancien_accueil.html", context)
            else:
                print(f"❌ ERREUR Candidat : {form_candidat.errors}")

    # Statistiques pour l'affichage
    context = {
        'nb_electeurs': Electeur.objects.count(),
        'nb_candidats': Candidat.objects.filter(cautionnement_valide=True).count(),
        'nb_votes': Vote.objects.count(),
        'form_electeur': form_electeur,
        'form_candidat': form_candidat,
    }
    return render(request, "ancien_accueil.html", context)



def resultats(request):
    candidats = Candidat.objects.annotate(total=Count('votes_recus'))
    total_votes = Vote.objects.count()
    
    classement = []
    for c in candidats:
        pourcentage = (c.total / total_votes * 100) if total_votes > 0 else 0
        classement.append({
            'candidat': c,
            'total': c.total,
            'pourcentage': round(pourcentage, 2),
        })
    
    # Trier par nombre de votes décroissant
    classement.sort(key=lambda x: x['total'], reverse=True)
    
    # Ajouter le rang
    for i, item in enumerate(classement):
        item['rang'] = i + 1
    
    context = {
        'classement': classement,
        'total_votes': total_votes,
    }
    return render(request, 'resultats.html', context)