# serveurcei/views.py — AVEC SAUVEGARDE EMPREINTE À L'INSCRIPTION

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db.models import Count
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Electeur, Candidat
from vote.models import ParticipationVote, BulletinVote
from .forms import ElecteurForm, CandidatForm
from .serializers import ElecteurSerializer


def accueil3(request):
    context = {
        'nb_electeurs': Electeur.objects.count(),
        'nb_candidats': Candidat.objects.filter(cautionnement_valide=True).count(),
        'nb_votes':     ParticipationVote.objects.count(),
    }
    return render(request, 'accueil3.html', context)


# ══════════════════════════════════════════════════
#  INSCRIPTION ÉLECTEUR — avec sauvegarde empreinte
# ══════════════════════════════════════════════════

def inscription_electeur(request):
    if request.method == 'POST':

        # ── Formulaire HTML classique ──
        if request.content_type != 'application/json':
            form = ElecteurForm(request.POST, request.FILES)
            if form.is_valid():
                electeur = form.save(commit=False)

                # ✅ Récupérer et sauvegarder le hash d'empreinte
                empreinte_hash = request.POST.get('empreinte_hash', '').strip()
                if empreinte_hash:
                    electeur.empreinte_hash = empreinte_hash
                else:
                    return render(request, 'inscription_electeur.html', {
                        'form': form,
                        'erreur_empreinte': "L'empreinte digitale est obligatoire pour l'inscription."
                    })

                electeur.save()
                return render(request, 'confirmation_inscription.html', {'electeur': electeur})
            else:
                return render(request, 'inscription_electeur.html', {
                    'form': form,
                    'errors': form.errors
                })

        # ── API JSON ──
        else:
            import json
            try:
                data = json.loads(request.body)
                electeur = Electeur.objects.create(
                    nom=data.get('nom'),
                    prenom=data.get('prenom'),
                    numero_cni=data.get('numero_cni'),
                    date_naissance=data.get('date_naissance'),
                    telephon=data.get('telephon'),
                    empreinte_hash=data.get('empreinte_hash', ''),
                )
                return JsonResponse({"message": "Inscrit", "numero": electeur.numero_electeur}, status=201)
            except Exception as e:
                return JsonResponse({"error": str(e)}, status=400)

    form = ElecteurForm()
    return render(request, 'inscription_electeur.html', {'form': form})


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
    participations = ParticipationVote.objects.all()
    return render(request, "votants.html", {"votes": participations})


def statistiques(request):
    return render(request, "statistiques.html")


def api_resultats(request):
    candidats   = Candidat.objects.annotate(total=Count('bulletinvote'))
    total_votes = BulletinVote.objects.count()
    data = []
    for c in candidats:
        pourcentage = (c.total / total_votes * 100) if total_votes > 0 else 0
        data.append({"nom": c.nom, "pourcentage": round(pourcentage, 2)})
    return JsonResponse(data, safe=False)


class ElecteurViewSet(viewsets.ModelViewSet):
    queryset = Electeur.objects.all()
    serializer_class = ElecteurSerializer


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
    form_electeur = ElecteurForm()
    form_candidat = CandidatForm()

    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        if form_type == 'electeur':
            form_electeur = ElecteurForm(request.POST, request.FILES)
            if form_electeur.is_valid():
                form_electeur.save()
                context = {'nb_electeurs': Electeur.objects.count(), 'nb_candidats': Candidat.objects.count()}
                return render(request, "ancien_accueil.html", context)
        elif form_type == 'candidat':
            form_candidat = CandidatForm(request.POST, request.FILES)
            if form_candidat.is_valid():
                form_candidat.save()
                context = {'nb_electeurs': Electeur.objects.count(), 'nb_candidats': Candidat.objects.count()}
                return render(request, "ancien_accueil.html", context)

    context = {
        'nb_electeurs' : Electeur.objects.count(),
        'nb_candidats' : Candidat.objects.filter(cautionnement_valide=True).count(),
        'nb_votes'     : ParticipationVote.objects.count(),
        'form_electeur': form_electeur,
        'form_candidat': form_candidat,
    }
    return render(request, "ancien_accueil.html", context)


def resultats(request):
    candidats   = Candidat.objects.annotate(total=Count('bulletinvote'))
    total_votes = BulletinVote.objects.count()
    classement  = []
    for c in candidats:
        pourcentage = (c.total / total_votes * 100) if total_votes > 0 else 0
        classement.append({'candidat': c, 'total': c.total, 'pourcentage': round(pourcentage, 2)})
    classement.sort(key=lambda x: x['total'], reverse=True)
    for i, item in enumerate(classement):
        item['rang'] = i + 1
    return render(request, 'resultats.html', {'classement': classement, 'total_votes': total_votes})