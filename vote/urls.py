from django.urls import path
from . import views

app_name = 'vote'

urlpatterns = [
    path('',                      views.page_vote,            name='page_vote'),
    path('voter/',                views.voter,                name='voter'),
    path('succes/',               views.vote_succes,          name='vote_succes'),
    path('verifier-empreinte/',   views.verifier_empreinte,   name='verifier_empreinte'),
    path('enregistrer-empreinte/',views.enregistrer_empreinte,name='enregistrer_empreinte'),
]