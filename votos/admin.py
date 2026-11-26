from django.contrib import admin
from .models import Candidato, EstadoVotacion, Papeleta, Voto


@admin.register(Candidato)
class CandidatoAdmin(admin.ModelAdmin):
    list_display = ('orden', 'nombre')
    ordering = ('orden',)


@admin.register(Papeleta)
class PapeletaAdmin(admin.ModelAdmin):
    list_display = ('id', 'fecha_hora')
    readonly_fields = ('fecha_hora',)


@admin.register(Voto)
class VotoAdmin(admin.ModelAdmin):
    list_display = ('candidato', 'papeleta', 'fecha_hora')
    list_filter = ('candidato',)


@admin.register(EstadoVotacion)
class EstadoVotacionAdmin(admin.ModelAdmin):
    list_display = ('cerrada', 'fecha_cierre')

    def has_add_permission(self, request):
        return False  # es una fila única (singleton)
