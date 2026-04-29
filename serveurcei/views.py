# serveurcei/views.py

import uuid, hashlib, json, random
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Q
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A6
from reportlab.lib.units import cm

from .models import (
    Electeur, Candidat, ParticipationVote, BulletinVote,
    AdminCEI, ActionLog, ElectionConfig
)
from .forms import ElecteurForm, CandidatForm
from .serializers import ElecteurSerializer


# ── Helpers admin ──
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def is_admin(request) -> bool:
    return bool(request.session.get('admin_id'))


# ══════════════════════════════════════════════════
#  ACCUEIL
# ══════════════════════════════════════════════════

def ancien_accueil(request):
    form_electeur = ElecteurForm()
    form_candidat = CandidatForm()

    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        if form_type == 'electeur':
            form_electeur = ElecteurForm(request.POST, request.FILES)
            if form_electeur.is_valid():
                form_electeur.save()
        elif form_type == 'candidat':
            form_candidat = CandidatForm(request.POST, request.FILES)
            if form_candidat.is_valid():
                form_candidat.save()

    context = {
        'nb_electeurs':  Electeur.objects.count(),
        'nb_candidats':  Candidat.objects.filter(cautionnement_valide=True).count(),
        'nb_votes':      ParticipationVote.objects.count(),
        'form_electeur': form_electeur,
        'form_candidat': form_candidat,
    }
    return render(request, 'ancien_accueil.html', context)


# ══════════════════════════════════════════════════
#  INSCRIPTIONS
# ══════════════════════════════════════════════════

def inscription_electeur(request):
    if request.method == 'POST':
        if request.content_type != 'application/json':
            form = ElecteurForm(request.POST, request.FILES)
            if form.is_valid():
                electeur = form.save(commit=False)
                empreinte_hash = request.POST.get('empreinte_hash', '').strip()

                if not empreinte_hash:
                    return render(request, 'inscription_electeur.html', {
                        'form': form,
                        'erreur_empreinte': "L'empreinte digitale est obligatoire."
                    })

                electeur.empreinte_hash = empreinte_hash
                electeur.save()

                request.session['inscription_success'] = {
                    'numero': electeur.numero_electeur,
                    'nom': electeur.nom,
                    'prenom': electeur.prenom,
                    'url_recu': reverse('serveurcei:telecharger_recu', args=[electeur.id])
                }
                return redirect('serveurcei:felicitations')
            else:
                print("ERREURS FORMULAIRE:", form.errors)
                return render(request, 'inscription_electeur.html', {
                    'form': form,
                    'errors': form.errors
                })
        else:
            try:
                data = json.loads(request.body)
                electeur = Electeur.objects.create(
                    nom=data.get('nom'),
                    prenom=data.get('prenom'),
                    numero_cni=data.get('numero_cni'),
                    date_naissance=data.get('date_naissance'),
                    telephon=data.get('telephone') or data.get('telephon'),
                    empreinte_hash=data.get('empreinte_hash', ''),
                )
                return JsonResponse({"message": "Inscrit", "numero": electeur.numero_electeur}, status=201)
            except Exception as e:
                return JsonResponse({"error": str(e)}, status=400)

    return render(request, 'inscription_electeur.html', {'form': ElecteurForm()})


def felicitations(request):
    if not request.session.get('inscription_success'):
        return redirect('serveurcei:inscription_electeur')

    context = {'electeur': request.session['inscription_success']}
    del request.session['inscription_success']
    return render(request, 'felicitations.html', context)


def inscription_candidat(request):
    if request.method == 'POST':
        form = CandidatForm(request.POST, request.FILES)
        if form.is_valid():
            candidat = form.save(commit=False)

            # ✅ Générer CNI et téléphone uniques automatiquement
            numero_cni_auto = f"CAND-{uuid.uuid4().hex[:8].upper()}"
            telephon_auto   = f"00{random.randint(1000000000, 9999999999)}"

            # ✅ Créer l'électeur automatiquement
            electeur = Electeur.objects.create(
                nom=candidat.nom,
                prenom=candidat.prenom,
                date_naissance=candidat.date_naissance,
                numero_cni=numero_cni_auto,
                telephon=telephon_auto,
                empreinte_hash='',
            )

            candidat.electeur = electeur
            candidat.save()

            request.session['candidat_success'] = {
                'id': candidat.id,
                'nom': candidat.nom,
                'prenom': candidat.prenom,
                'parti_politique': candidat.parti_politique,
                'date_naissance': str(candidat.date_naissance),
                'cautionnement_valide': candidat.cautionnement_valide,
                # ✅ Numéro électeur généré automatiquement
                'numero_electeur': electeur.numero_electeur,
                'url_recu': reverse('serveurcei:telecharger_recu_candidat', args=[candidat.id])
            }
            return redirect('serveurcei:felicitations_candidat')
    else:
        form = CandidatForm()
    return render(request, 'inscription_candidat.html', {'form': form})


def felicitations_candidat(request):
    if not request.session.get('candidat_success'):
        return redirect('serveurcei:inscription_candidat')
    context = {
        'candidat': request.session['candidat_success'],
        'url_recu': request.session['candidat_success']['url_recu']
    }
    del request.session['candidat_success']
    return render(request, 'felicitations_candidat.html', context)


# ══════════════════════════════════════════════════
#  API ÉLECTEURS
# ══════════════════════════════════════════════════

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


class ElecteurViewSet(viewsets.ModelViewSet):
    queryset = Electeur.objects.all()
    serializer_class = ElecteurSerializer


# ══════════════════════════════════════════════════
#  EMPREINTES
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

    try:
        electeur = Electeur.objects.get(numero_electeur=numero_electeur)
    except Electeur.DoesNotExist:
        return JsonResponse({'ok': False, 'erreur': "Numéro d'électeur introuvable."})

    if not electeur.empreinte_hash:
        return JsonResponse({'ok': False, 'erreur': "Aucune empreinte enregistrée."})

    if electeur.empreinte_hash != empreinte_hash:
        return JsonResponse({'ok': False, 'erreur': "Empreinte non reconnue."})

    if ParticipationVote.objects.filter(electeur=electeur).exists():
        return JsonResponse({'ok': False, 'erreur': f"{numero_electeur} a déjà voté."})

    return JsonResponse({'ok': True, 'message': "Identité confirmée. Vous pouvez voter."})


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


# ══════════════════════════════════════════════════
#  VOTE
# ══════════════════════════════════════════════════

def page_vote(request):
    candidats = Candidat.objects.filter(cautionnement_valide=True)
    return render(request, 'vote.html', {'candidats': candidats})


def voter(request):
    if request.method != 'POST':
        return redirect('serveurcei:page_vote')

    numero_electeur = request.POST.get('numero_electeur', '').strip()
    candidat_id     = request.POST.get('candidat_id', '').strip()
    empreinte_hash  = request.POST.get('empreinte_hash', '').strip()

    if not candidat_id:
        messages.error(request, "⚠️ Veuillez sélectionner un candidat.")
        return redirect('serveurcei:page_vote')
    if not numero_electeur:
        messages.error(request, "⚠️ Veuillez entrer votre numéro d'électeur.")
        return redirect('serveurcei:page_vote')
    if not empreinte_hash:
        messages.error(request, "⚠️ La vérification d'empreinte est obligatoire.")
        return redirect('serveurcei:page_vote')

    try:
        candidat = Candidat.objects.get(id=candidat_id)
    except Candidat.DoesNotExist:
        messages.error(request, "❌ Ce candidat n'existe pas.")
        return redirect('serveurcei:page_vote')

    try:
        electeur = Electeur.objects.get(numero_electeur=numero_electeur)
    except Electeur.DoesNotExist:
        messages.error(request, "❌ Numéro d'électeur introuvable.")
        return redirect('serveurcei:page_vote')

    if not electeur.empreinte_hash or electeur.empreinte_hash != empreinte_hash:
        messages.error(request, "❌ Empreinte digitale non reconnue. Vote refusé.")
        return redirect('serveurcei:page_vote')

    if ParticipationVote.objects.filter(electeur=electeur).exists():
        messages.error(request, f"⚠️ {numero_electeur} a déjà voté.")
        return redirect('serveurcei:page_vote')

    try:
        with transaction.atomic():
            jeton = uuid.uuid4()
            ParticipationVote.objects.create(electeur=electeur, jeton_utilise=jeton)
            BulletinVote.objects.create(
                candidat=candidat,
                jeton_hash=hashlib.sha256(str(jeton).encode()).hexdigest()
            )
    except Exception:
        messages.error(request, "❌ Une erreur est survenue. Veuillez réessayer.")
        return redirect('serveurcei:page_vote')

    messages.success(request, f"✅ Vote pour {candidat.nom} {candidat.prenom} enregistré !")
    return redirect('serveurcei:page_vote')


def vote_succes(request):
    return render(request, 'succes_vote.html')


# ══════════════════════════════════════════════════
#  STATISTIQUES ET RÉSULTATS
# ══════════════════════════════════════════════════

def votants(request):
    participations = ParticipationVote.objects.all()
    return render(request, 'votants.html', {'votes': participations})


def statistiques(request):
    return render(request, 'statistiques.html')


def api_resultats(request):
    candidats   = Candidat.objects.annotate(total=Count('bulletinvote'))
    total_votes = BulletinVote.objects.count()
    data = []
    for c in candidats:
        pourcentage = (c.total / total_votes * 100) if total_votes > 0 else 0
        data.append({"nom": c.nom, "pourcentage": round(pourcentage, 2)})
    return JsonResponse(data, safe=False)


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


# ══════════════════════════════════════════════════
#  REÇU PDF — ÉLECTEUR
# ══════════════════════════════════════════════════

def telecharger_recu_cei(request, electeur_id):
    try:
        electeur = Electeur.objects.get(id=electeur_id)
    except Electeur.DoesNotExist:
        return HttpResponse("Électeur non trouvé", status=404)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Recu_CEI_{electeur.numero_electeur}.pdf"'

    p = canvas.Canvas(response, pagesize=A6)
    width, height = A6

    p.setStrokeColorRGB(0, 0.62, 0.38)
    p.rect(0.5*cm, 0.5*cm, width - 1*cm, height - 1*cm, stroke=1, fill=0)

    p.setFont("Helvetica-Bold", 12)
    p.drawCentredString(width/2, height - 1.5*cm, "REPUBLIQUE DE COTE D'IVOIRE")
    p.setFont("Helvetica", 8)
    p.drawCentredString(width/2, height - 2*cm, "Commission Electorale Independante (CEI)")

    p.setStrokeColorRGB(0.97, 0.45, 0.08)
    p.line(1*cm, height - 2.5*cm, width - 1*cm, height - 2.5*cm)

    p.setFillColorRGB(0, 0, 0)
    p.setFont("Helvetica-Bold", 10)
    p.drawString(1*cm, height - 3.5*cm, f"NOM       : {electeur.nom.upper()}")
    p.drawString(1*cm, height - 4.3*cm, f"PRENOMS   : {electeur.prenom}")
    p.drawString(1*cm, height - 5.1*cm, f"CNI       : {electeur.numero_cni}")
    p.drawString(1*cm, height - 5.9*cm, f"TEL       : {electeur.telephon}")

    p.setFillColorRGB(0.97, 0.45, 0.08)
    p.setFont("Helvetica-Bold", 11)
    p.drawCentredString(width/2, 4.2*cm, "NUMERO ELECTEUR CEI :")
    p.setFont("Helvetica-Bold", 20)
    p.drawCentredString(width/2, 3.2*cm, f"{electeur.numero_electeur}")

    p.setFillColorRGB(0, 0.62, 0.38)
    p.setFont("Helvetica-Bold", 8)
    p.drawCentredString(width/2, 2.2*cm, "ELECTEUR INSCRIT")

    p.setFillColorRGB(0.4, 0.4, 0.4)
    p.setFont("Helvetica-Oblique", 7)
    p.drawCentredString(width/2, 1*cm, "Gardez ce numero precieusement pour le jour du vote.")

    p.showPage()
    p.save()
    return response


# ══════════════════════════════════════════════════
#  ADMINISTRATION CEI
# ══════════════════════════════════════════════════

def admin_login(request):
    if request.session.get('admin_id'):
        return redirect('serveurcei:admin_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        if not username or not password:
            messages.error(request, "Veuillez remplir tous les champs.")
            return render(request, 'admin_login.html')

        admin = AdminCEI.objects.filter(username=username, is_active=True).first()
        if admin and admin.password_hash == hash_password(password):
            request.session['admin_id'] = admin.id
            admin.last_login = timezone.now()
            admin.save(update_fields=['last_login'])
            return redirect('serveurcei:admin_dashboard')

        messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")

    return render(request, 'admin_login.html')


def admin_dashboard(request):
    if not is_admin(request):
        return redirect('serveurcei:admin_login')
    return render(request, 'admin_dashboard.html', {
        'total_electeurs': Electeur.objects.count(),
        'total_votes':     BulletinVote.objects.count(),
        'total_candidats': Candidat.objects.count(),
    })


def admin_electeurs(request):
    if not is_admin(request):
        return redirect('serveurcei:admin_login')

    search = request.GET.get('search', '').strip()
    filtre = request.GET.get('filtre', 'tous')

    electeurs = Electeur.objects.all().order_by('nom')

    if search:
        electeurs = electeurs.filter(
            Q(nom__icontains=search) |
            Q(prenom__icontains=search) |
            Q(numero_cni__icontains=search) |
            Q(numero_electeur__icontains=search)
        )

    if filtre == 'vivants':
        electeurs = electeurs.filter(is_alive=True)
    elif filtre == 'decedes':
        electeurs = electeurs.filter(is_alive=False)
    elif filtre == 'ont_vote':
        electeurs = electeurs.filter(participation__isnull=False)
    elif filtre == 'pas_vote':
        electeurs = electeurs.filter(participation__isnull=True)

    return render(request, 'admin_electeurs.html', {
        'electeurs': electeurs,
        'search': search,
        'filtre': filtre,
    })


def admin_supprimer_electeur(request, electeur_id):
    if not is_admin(request):
        return redirect('serveurcei:admin_login')
    get_object_or_404(Electeur, id=electeur_id).delete()
    messages.success(request, "Électeur supprimé.")
    return redirect('serveurcei:admin_electeurs')


def admin_toggle_deces(request, electeur_id):
    if not is_admin(request):
        return redirect('serveurcei:admin_login')
    e = get_object_or_404(Electeur, id=electeur_id)
    e.is_alive = not e.is_alive
    e.save()
    return redirect('serveurcei:admin_electeurs')


def admin_resultats(request):
    if not is_admin(request):
        return redirect('serveurcei:admin_login')
    candidats   = Candidat.objects.annotate(total=Count('bulletinvote')).order_by('-total')
    total_votes = BulletinVote.objects.count()
    classement  = []
    for i, c in enumerate(candidats):
        pourcentage = (c.total / total_votes * 100) if total_votes > 0 else 0
        classement.append({
            'candidat':    c,
            'total':       c.total,
            'pourcentage': round(pourcentage, 2),
            'rang':        i + 1,
        })
    return render(request, 'admin_resultats.html', {
        'classement':   classement,
        'total_votes':  total_votes,
    })


def admin_statistiques(request):
    if not is_admin(request):
        return redirect('serveurcei:admin_login')

    total_inscrits     = Electeur.objects.count()
    total_votes        = BulletinVote.objects.count()
    abstentions        = total_inscrits - total_votes
    taux_participation = round((total_votes / total_inscrits * 100), 2) if total_inscrits > 0 else 0
    ont_vote           = total_votes

    candidats = Candidat.objects.annotate(total=Count('bulletinvote')).order_by('-total')
    data_candidats = []
    for c in candidats:
        data_candidats.append({
            'nom':   f"{c.nom} {c.prenom}",
            'parti': c.parti_politique,
            'votes': c.total,
        })

    from django.db.models.functions import TruncDate
    votes_par_jour = list(
        BulletinVote.objects
        .annotate(date=TruncDate('date_vote'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
        .values('date', 'count')
    )
    votes_par_jour_json = json.dumps([
        {'date': str(v['date']), 'count': v['count']}
        for v in votes_par_jour
    ])

    import json as json_mod
    return render(request, 'admin_statistiques.html', {
        'total_inscrits':      total_inscrits,
        'total_votes':         total_votes,
        'abstentions':         max(0, abstentions),
        'taux_participation':  taux_participation,
        'ont_vote':            ont_vote,
        'data_candidats_json': json_mod.dumps(data_candidats),
        'votes_par_jour':      votes_par_jour_json,
    })


def admin_logs(request):
    if not is_admin(request):
        return redirect('serveurcei:admin_login')
    return render(request, 'admin_logs.html', {
        'logs': ActionLog.objects.all().order_by('-timestamp')
    })


def admin_election(request):
    if not is_admin(request):
        return redirect('serveurcei:admin_login')
    return render(request, 'admin_election.html', {
        'config': ElectionConfig.objects.first()
    })


def admin_candidats(request):
    if not is_admin(request):
        return redirect('serveurcei:admin_login')
    return render(request, 'admin_candidats.html', {
        'candidats': Candidat.objects.all()
    })


def admin_toggle_candidat(request, candidat_id):
    if not is_admin(request):
        return redirect('serveurcei:admin_login')
    c = get_object_or_404(Candidat, id=candidat_id)
    c.cautionnement_valide = not c.cautionnement_valide
    c.save()
    return redirect('serveurcei:admin_candidats')


def admin_deconnexion(request):
    request.session.pop('admin_id', None)
    return redirect('serveurcei:admin_login')


# ══════════════════════════════════════════════════
#  REÇU PDF — CANDIDAT
# ══════════════════════════════════════════════════

def telecharger_recu_candidat(request, candidat_id):
    try:
        candidat = Candidat.objects.get(id=candidat_id)
    except Candidat.DoesNotExist:
        return HttpResponse("Candidat non trouvé", status=404)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Recu_Candidat_{candidat.nom}.pdf"'

    p = canvas.Canvas(response, pagesize=A6)
    width, height = A6

    # Bordure verte
    p.setStrokeColorRGB(0, 0.62, 0.38)
    p.rect(0.5*cm, 0.5*cm, width - 1*cm, height - 1*cm, stroke=1, fill=0)

    # En-tête
    p.setFont("Helvetica-Bold", 12)
    p.drawCentredString(width/2, height - 1.5*cm, "REPUBLIQUE DE COTE D'IVOIRE")
    p.setFont("Helvetica", 8)
    p.drawCentredString(width/2, height - 2*cm, "Commission Electorale Independante (CEI)")

    # Ligne orange
    p.setStrokeColorRGB(0.97, 0.45, 0.08)
    p.line(1*cm, height - 2.5*cm, width - 1*cm, height - 2.5*cm)

    # ✅ Photo du candidat
    if candidat.photo:
        try:
            from reportlab.lib.utils import ImageReader
            img = ImageReader(candidat.photo.path)
            p.drawImage(img, width - 4*cm, height - 5.8*cm,
                        width=3*cm, height=3*cm,
                        preserveAspectRatio=True, mask='auto')
        except Exception:
            pass

    # Informations
    p.setFillColorRGB(0, 0, 0)
    p.setFont("Helvetica-Bold", 10)
    p.drawString(1*cm, height - 3.5*cm, f"NOM       : {candidat.nom.upper()}")
    p.drawString(1*cm, height - 4.3*cm, f"PRENOMS   : {candidat.prenom}")
    p.drawString(1*cm, height - 5.1*cm, f"PARTI     : {candidat.parti_politique}")
    p.drawString(1*cm, height - 5.9*cm, f"CAUTION   : {'Validee' if candidat.cautionnement_valide else 'En attente'}")
    p.drawString(1*cm, height - 6.7*cm, f"NE(E) LE  : {candidat.date_naissance}")

    # ✅ Numéro électeur
    numero_electeur = candidat.electeur.numero_electeur if candidat.electeur else "NON ASSIGNE"
    p.setFillColorRGB(0.97, 0.45, 0.08)
    p.setFont("Helvetica-Bold", 11)
    p.drawCentredString(width/2, 4.2*cm, "NUMERO ELECTEUR CEI :")
    p.setFont("Helvetica-Bold", 18)
    p.drawCentredString(width/2, 3.2*cm, numero_electeur)

    # Statut
    p.setFillColorRGB(0, 0.62, 0.38)
    p.setFont("Helvetica-Bold", 8)
    p.drawCentredString(width/2, 2.2*cm, "CANDIDAT & ELECTEUR INSCRIT")

    # Pied de page
    p.setFillColorRGB(0.4, 0.4, 0.4)
    p.setFont("Helvetica-Oblique", 7)
    p.drawCentredString(width/2, 1*cm, "Gardez ce numero precieusement pour le jour du vote.")

    p.showPage()
    p.save()
    return response