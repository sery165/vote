from django.urls import path
from . import views

urlpatterns = [
    path('',        views.page_vote,      name='page_vote'),
    path('voter/',  views.soumettre_vote, name='voter'),
    path('succes/', views.vote_succes,    name='vote_succes'),
]