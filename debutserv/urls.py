from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from serveurcei import views as cei_views

urlpatterns = [
    path('admin/',         admin.site.urls),
    path('',               cei_views.page_vote,    name='page_vote'),
    path('votants/',       cei_views.votants,       name='votants'),
    path('statistiques/',  cei_views.statistiques,  name='statistiques'),
    path('api-resultats/', cei_views.api_resultats, name='api_resultats'),
    path('',           include('serveurcei.urls', namespace='serveurcei')),
    path('api-auth/',      include('rest_framework.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)