from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from .models import MAX_VOTOS_POR_PAPELETA, Candidato, EstadoVotacion, Papeleta, Voto
from .reportes import calcular_resumen, enviar_resultados_por_correo


def registrar_voto(request):
    """
    Pantalla del operador: se escriben los números de los candidatos que
    eligió un participante (entre 1 y MAX_VOTOS_POR_PAPELETA) y se registran
    todos juntos como una papeleta.
    """
    error = None
    texto_ingresado = ''
    mensaje_exito = None

    if request.method == 'POST':
        texto_ingresado = request.POST.get('numeros', '').strip()
        numeros_texto = [n for n in texto_ingresado.replace(',', ' ').split() if n]

        if len(numeros_texto) == 0:
            error = 'Debes ingresar al menos 1 número de candidato.'
        elif len(numeros_texto) > MAX_VOTOS_POR_PAPELETA:
            error = f'Puedes elegir como máximo {MAX_VOTOS_POR_PAPELETA} candidatos (ingresaste {len(numeros_texto)}).'
        elif not all(n.isdigit() for n in numeros_texto):
            error = 'Todos los valores deben ser números.'
        else:
            numeros = [int(n) for n in numeros_texto]
            if len(set(numeros)) != len(numeros):
                error = 'No puedes repetir el mismo número de candidato en una misma papeleta.'
            else:
                candidatos = list(Candidato.objects.filter(orden__in=numeros))
                if len(candidatos) != len(numeros):
                    encontrados = {c.orden for c in candidatos}
                    faltantes = [n for n in numeros if n not in encontrados]
                    error = f'No existe un candidato con el número: {", ".join(str(n) for n in faltantes)}.'
                else:
                    papeleta = Papeleta.objects.create()
                    Voto.objects.bulk_create(
                        Voto(papeleta=papeleta, candidato=c) for c in candidatos
                    )
                    mensaje_exito = f'Papeleta #{papeleta.id} registrada con éxito.'
                    texto_ingresado = ''

    candidatos = Candidato.objects.all()
    total_participantes = Papeleta.objects.count()

    return render(request, 'votos/registrar_voto.html', {
        'candidatos': candidatos,
        'error': error,
        'texto_ingresado': texto_ingresado,
        'mensaje_exito': mensaje_exito,
        'total_participantes': total_participantes,
        'max_votos_por_papeleta': MAX_VOTOS_POR_PAPELETA,
    })


def resultados_en_vivo(request):
    """Pantalla para proyectar/mirar mientras se van ingresando los votos."""
    return render(request, 'votos/resultados_en_vivo.html', {
        'max_votos_por_papeleta': MAX_VOTOS_POR_PAPELETA,
        # Textos y logo configurables desde el .env (ver settings.py).
        'votacion_titulo': settings.VOTACION_TITULO,
        'votacion_subtitulo_electos': settings.VOTACION_SUBTITULO_ELECTOS,
        'organizacion_logo': settings.ORGANIZACION_LOGO,
        'organizacion_nombre': settings.ORGANIZACION_NOMBRE,
    })


def resultados_en_vivo_datos(request):
    """Endpoint JSON que la pantalla de resultados en vivo consulta periódicamente."""
    filas, total_participantes, texto_ganador, texto_corte = calcular_resumen()
    fotos_por_candidato = {
        c.nombre: (c.foto.url if c.foto else None)
        for c in Candidato.objects.all()
    }
    return JsonResponse({
        'cerrada': EstadoVotacion.actual().cerrada,
        'total_participantes': total_participantes,
        'texto_ganador': texto_ganador,
        'texto_corte': texto_corte,
        'candidatos': [
            {
                'numero': fila['numero'],
                'nombre': fila['nombre'],
                'votos': fila['votos'],
                'porcentaje': round(fila['porcentaje'], 2),
                'electo': fila['electo'],
                'foto_url': fotos_por_candidato.get(fila['nombre']),
            }
            for fila in filas
        ],
    })


@staff_member_required
def cerrar_votacion(request):
    """
    Botón manual para el organizador: envía por correo el Excel con los
    resultados actuales, sin tocar ni borrar ningún dato de la votación.
    """
    enviado = None

    if request.method == 'POST':
        try:
            enviado = enviar_resultados_por_correo(
                asunto='Votación cerrada - resultados',
                cuerpo=(
                    'El organizador cerró la votación desde el panel. Adjunto el Excel '
                    'con el resumen: participantes, votos y porcentaje por candidato, '
                    'el directorio electo (7 cupos) y un gráfico de votos. '
                    'Las papeletas y votos no fueron modificados.'
                ),
            )
        except Exception:
            enviado = False

        estado = EstadoVotacion.actual()
        estado.cerrada = True
        estado.fecha_cierre = timezone.now()
        estado.save()

    return render(request, 'votos/cerrar_votacion.html', {'enviado': enviado})


@staff_member_required
def reiniciar_votacion(request):
    """
    Botón manual para el organizador: borra TODAS las papeletas y votos
    para dejar el conteo en cero. Requiere confirmación explícita porque
    no se puede deshacer.
    """
    total_papeletas = Papeleta.objects.count()
    reiniciado = False

    if request.method == 'POST':
        if request.POST.get('confirmacion') == 'REINICIAR':
            Papeleta.objects.all().delete()  # borra en cascada los Voto asociados
            with connection.cursor() as cursor:
                # Reinicia el contador de "N° de papeleta" para que la próxima
                # papeleta vuelva a empezar en el #1 (si no, SQLite seguía
                # numerando desde donde había quedado antes del reinicio).
                cursor.execute(
                    'DELETE FROM sqlite_sequence WHERE name = %s',
                    [Papeleta._meta.db_table],
                )
            estado = EstadoVotacion.actual()
            estado.cerrada = False
            estado.fecha_cierre = None
            estado.save()
            reiniciado = True
            total_papeletas = 0
        else:
            return render(request, 'votos/reiniciar_votacion.html', {
                'total_papeletas': total_papeletas,
                'reiniciado': False,
                'error': 'Debes escribir REINICIAR (en mayúsculas) para confirmar.',
            })

    return render(request, 'votos/reiniciar_votacion.html', {
        'total_papeletas': total_papeletas,
        'reiniciado': reiniciado,
        'error': None,
    })
