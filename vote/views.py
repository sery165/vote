# vote/views.py — AVEC VÉRIFICATION EMPREINTE DIGITALE

import uuid, hashlib, json
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import ParticipationVote, BulletinVote
from serveurcei.models import Candidat, Electeur


# ══════════════════════════════════════════════════
#  PAGE PRINCIPALE DE VOTE
# ══════════════════════════════════════════════════

def page_vote(request):
    candidats = Candidat.objects.filter(cautionnement_valide=True)
    return render(request, 'vote.html', {'candidats': candidats})


# ══════════════════════════════════════════════════
#  VÉRIFICATION EMPREINTE (appelée en AJAX avant vote)
#  POST /vote/verifier-empreinte/
#  Body JSON : { "numero_electeur": "CEI-XXX", "empreinte_hash": "abc123..." }
# ══════════════════════════════════════════════════

@csrf_exempt
def verifier_empreinte(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'erreur': 'Méthode non autorisée'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'erreur': 'Données invalides'}, status=400)

    numero_electeur = data.get('numero_electeur', '').strip()
    empreinte_hash  = data.get('empreinte_hash', '').strip()

    if not numero_electeur or not empreinte_hash:
        return JsonResponse({'ok': False, 'erreur': 'Données manquantes'}, status=400)

    # Chercher l'électeur
    try:
        electeur = Electeur.objects.get(numero_electeur=numero_electeur)
    except Electeur.DoesNotExist:
        return JsonResponse({'ok': False, 'erreur': "Numéro d'électeur introuvable."})

    # Vérifier empreinte
    if not electeur.empreinte_hash:
        return JsonResponse({'ok': False, 'erreur': "Aucune empreinte enregistrée pour cet électeur."})

    if electeur.empreinte_hash != empreinte_hash:
        return JsonResponse({'ok': False, 'erreur': "Empreinte non reconnue. Identité non confirmée."})

    # Vérifier s'il a déjà voté
    if ParticipationVote.objects.filter(electeur=electeur).exists():
        return JsonResponse({'ok': False, 'erreur': f"Le numéro {numero_electeur} a déjà voté."})

    return JsonResponse({'ok': True, 'message': "Identité confirmée. Vous pouvez voter."})


# ══════════════════════════════════════════════════
#  SOUMISSION DU VOTE (après vérification empreinte)
# ══════════════════════════════════════════════════

def voter(request):
    if request.method != 'POST':
        return redirect('vote:page_vote')

    numero_electeur = request.POST.get('numero_electeur', '').strip()
    candidat_id     = request.POST.get('candidat_id', '').strip()
    empreinte_hash  = request.POST.get('empreinte_hash', '').strip()

    # ── 1. Champs obligatoires ──
    if not candidat_id:
        messages.error(request, "⚠️ Veuillez sélectionner un candidat.")
        return redirect('vote:page_vote')

    if not numero_electeur:
        messages.error(request, "⚠️ Veuillez entrer votre numéro d'électeur.")
        return redirect('vote:page_vote')

    if not empreinte_hash:
        messages.error(request, "⚠️ La vérification d'empreinte est obligatoire.")
        return redirect('vote:page_vote')

    # ── 2. Candidat existe ? ──
    try:
        candidat = Candidat.objects.get(id=candidat_id)
    except Candidat.DoesNotExist:
        messages.error(request, "❌ Ce candidat n'existe pas.")
        return redirect('vote:page_vote')

    # ── 3. Électeur existe ? ──
    try:
        electeur = Electeur.objects.get(numero_electeur=numero_electeur)
    except Electeur.DoesNotExist:
        messages.error(request, "❌ Numéro d'électeur introuvable. Vérifiez votre carte CEI.")
        return redirect('vote:page_vote')

    # ── 4. Vérification empreinte (double contrôle côté serveur) ──
    if not electeur.empreinte_hash:
        messages.error(request, "❌ Aucune empreinte enregistrée pour cet électeur.")
        return redirect('vote:page_vote')

    if electeur.empreinte_hash != empreinte_hash:
        messages.error(request, "❌ Empreinte digitale non reconnue. Vote refusé.")
        return redirect('vote:page_vote')

    # ── 5. A déjà voté ? ──
    if ParticipationVote.objects.filter(electeur=electeur).exists():
        messages.error(request, f"⚠️ Le numéro {numero_electeur} a déjà été utilisé pour voter.")
        return redirect('vote:page_vote')

    # ── 6. Enregistrement sécurisé ──
    try:
        with transaction.atomic():
            jeton = uuid.uuid4()
            ParticipationVote.objects.create(
                electeur=electeur,
                jeton_utilise=jeton
            )
            BulletinVote.objects.create(
                candidat=candidat,
                jeton_hash=hashlib.sha256(str(jeton).encode()).hexdigest()
            )
    except Exception:
        messages.error(request, "❌ Une erreur est survenue. Veuillez réessayer.")
        return redirect('vote:page_vote')

    # ── 7. Succès ──
    messages.success(request, f"✅ Félicitations ! Votre vote pour {candidat.nom} {candidat.prenom} a bien été enregistré.")
    return redirect('vote:page_vote')


# ══════════════════════════════════════════════════
#  ENREGISTRER EMPREINTE (lors de l'inscription)
#  POST /vote/enregistrer-empreinte/
#  Body JSON : { "numero_electeur": "CEI-XXX", "empreinte_hash": "abc123..." }
# ══════════════════════════════════════════════════

@csrf_exempt
def enregistrer_empreinte(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'erreur': 'Méthode non autorisée'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'erreur': 'Données invalides'}, status=400)

    numero_electeur = data.get('numero_electeur', '').strip()
    empreinte_hash  = data.get('empreinte_hash', '').strip()

    if not numero_electeur or not empreinte_hash:
        return JsonResponse({'ok': False, 'erreur': 'Données manquantes'}, status=400)

    try:
        electeur = Electeur.objects.get(numero_electeur=numero_electeur)
    except Electeur.DoesNotExist:
        return JsonResponse({'ok': False, 'erreur': "Électeur introuvable."})

    electeur.empreinte_hash = empreinte_hash
    electeur.save(update_fields=['empreinte_hash'])

    return JsonResponse({'ok': True, 'message': "Empreinte enregistrée avec succès."})


def vote_succes(request):
    return render(request, 'vote/succes.html')