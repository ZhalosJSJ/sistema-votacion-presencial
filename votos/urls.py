from django.urls import path
from . import views

app_name = 'votos'

urlpatterns = [
    path('', views.registrar_voto, name='registrar_voto'),
    path('resultados-en-vivo/', views.resultados_en_vivo, name='resultados_en_vivo'),
    path('resultados-en-vivo/datos/', views.resultados_en_vivo_datos, name='resultados_en_vivo_datos'),
    path('organizador/cerrar-votacion/', views.cerrar_votacion, name='cerrar_votacion'),
    path('organizador/reiniciar-votacion/', views.reiniciar_votacion, name='reiniciar_votacion'),
]
