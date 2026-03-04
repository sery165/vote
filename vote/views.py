from django.shortcuts import render, redirect
from django.contrib import messages
from serveurcei.models import Electeur, Candidat
from .models import Vote


def page_vote(request):
    candidats = Candidat.objects.filter(
        cautionnement_valide=True
    ).order_by('nom')
    return render(request, 'vote.html', {'candidats': candidats})


def soumettre_vote(request):
    if request.method != 'POST':
        return redirect('page_vote')

    candidat_id     = request.POST.get('candidat_id', '').strip()
    # ✅ CORRECTION : strip() seulement, PAS de .upper()
    numero_electeur = request.POST.get('numero_electeur', '').strip()

    # 1. Candidat sélectionné ?
    if not candidat_id:
        messages.error(request, 'Veuillez sélectionner un candidat.')
        return redirect('page_vote')

    # 2. Numéro fourni ?
    if not numero_electeur:
        messages.error(request, "Veuillez entrer votre numéro d'électeur.")
        return redirect('page_vote')

    # 3. L'électeur existe-t-il ?
    # ✅ CORRECTION : recherche insensible à la casse avec __iexact
    try:
        electeur = Electeur.objects.get(
            numero_electeur__iexact=numero_electeur
        )
    except Electeur.DoesNotExist:
        messages.error(
            request,
            f'❌ Numéro « {numero_electeur} » introuvable. '
            f'Vérifiez votre carte d\'électeur CEI.'
        )
        return redirect('page_vote')

    # ✅ SUPPRIMÉ : l'étape 4 inutile qui bloquait

    # 4. A-t-il déjà voté ?
    if Vote.objects.filter(electeur=electeur).exists():
        messages.error(
            request,
            f'⚠️ {electeur.nom} {electeur.prenom}, vous avez déjà voté. '
            f'Un seul vote est autorisé par électeur.'
        )
        return redirect('page_vote')

    # 5. Le candidat est-il valide ?
    try:
        candidat = Candidat.objects.get(
            id=candidat_id,
            cautionnement_valide=True
        )
    except Candidat.DoesNotExist:
        messages.error(request, '❌ Candidat invalide ou non autorisé.')
        return redirect('page_vote')

    # 6. Enregistrer le vote ✅
    Vote.objects.create(electeur=electeur, candidat=candidat)
    return redirect('vote_succes')


def vote_succes(request):
    return render(request, 'succes.html')