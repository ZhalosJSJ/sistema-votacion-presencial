"""Genera el resumen de resultados (participación, votos por candidato y directorio electo)."""
from django.conf import settings
from django.core.mail import EmailMessage
from django.db.models import Count
from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Alignment, Font, PatternFill

from .models import CUPOS_DIRECTORIO, Candidato, Papeleta

RUTA_EXCEL = 'resultados_votacion.xlsx'


def calcular_resumen():
    """
    Devuelve (filas, total_participantes, texto_ganador, texto_corte).
    `filas` es una lista de dicts: numero, nombre, votos, porcentaje, electo (bool),
    ordenada por ranking (más votado primero). `numero` es el número fijo del
    candidato (Candidato.orden) y nunca cambia; solo cambia su posición en la lista.
    El porcentaje se calcula sobre el total de votos contabilizados (no sobre
    la cantidad de participantes), ya que cada participante puede emitir varios votos.
    """
    total_participantes = Papeleta.objects.count()

    candidatos = (
        Candidato.objects
        .annotate(num_votos=Count('votos'))
        .order_by('-num_votos', 'orden')
    )
    total_votos = sum(c.num_votos for c in candidatos)

    filas = []
    for posicion, c in enumerate(candidatos, start=1):
        porcentaje = (c.num_votos / total_votos * 100) if total_votos else 0
        filas.append({
            'numero': c.orden,
            'nombre': c.nombre,
            'votos': c.num_votos,
            'porcentaje': porcentaje,
            'electo': posicion <= CUPOS_DIRECTORIO,
        })

    texto_ganador = None
    if len(filas) >= 2 and total_participantes:
        primero, segundo = filas[0], filas[1]
        margen_votos = primero['votos'] - segundo['votos']
        margen_pct = primero['porcentaje'] - segundo['porcentaje']
        texto_ganador = (
            f"Más votado: {primero['nombre']} con {margen_votos} votos de ventaja "
            f"({margen_pct:.2f} puntos porcentuales) sobre {segundo['nombre']}."
        )
    elif len(filas) == 1 and total_participantes:
        texto_ganador = f"Más votado: {filas[0]['nombre']} (candidato único)."

    texto_corte = None
    if len(filas) > CUPOS_DIRECTORIO and total_participantes:
        ultimo_electo = filas[CUPOS_DIRECTORIO - 1]
        primer_no_electo = filas[CUPOS_DIRECTORIO]
        margen_votos = ultimo_electo['votos'] - primer_no_electo['votos']
        margen_pct = ultimo_electo['porcentaje'] - primer_no_electo['porcentaje']
        texto_corte = (
            f"Margen del último cupo: {ultimo_electo['nombre']} (electo, puesto {CUPOS_DIRECTORIO}) "
            f"le gana por {margen_votos} votos ({margen_pct:.2f} puntos porcentuales) a "
            f"{primer_no_electo['nombre']} (primer suplente, puesto {CUPOS_DIRECTORIO + 1})."
        )

    return filas, total_participantes, texto_ganador, texto_corte


def generar_excel(ruta=RUTA_EXCEL):
    """Construye el archivo Excel con el resumen, el directorio electo y un gráfico de votos."""
    filas, total_participantes, texto_ganador, texto_corte = calcular_resumen()

    libro = Workbook()
    hoja = libro.active
    hoja.title = 'Resultados'

    negrita = Font(bold=True)
    verde_electo = PatternFill(start_color='D9F2D9', end_color='D9F2D9', fill_type='solid')

    hoja['A1'] = f'Resultados - {settings.VOTACION_TITULO}'
    hoja['A1'].font = Font(bold=True, size=14)

    hoja['A3'] = 'Participantes que votaron'
    hoja['B3'] = total_participantes
    hoja['A3'].font = negrita

    fila_inicio_tabla = 5
    encabezados = ['N°', 'Candidato', 'Votos', '% del total de votos', 'Electo']
    for col, encabezado in enumerate(encabezados, start=1):
        celda = hoja.cell(row=fila_inicio_tabla, column=col, value=encabezado)
        celda.font = negrita

    fila_actual = fila_inicio_tabla + 1
    fila_datos_inicio = fila_actual
    for fila in filas:
        hoja.cell(row=fila_actual, column=1, value=fila['numero'])
        hoja.cell(row=fila_actual, column=2, value=fila['nombre'])
        hoja.cell(row=fila_actual, column=3, value=fila['votos'])
        hoja.cell(row=fila_actual, column=4, value=f"{fila['porcentaje']:.2f}%")
        hoja.cell(row=fila_actual, column=5, value='Sí' if fila['electo'] else '')
        if fila['electo']:
            for col in range(1, 6):
                hoja.cell(row=fila_actual, column=col).fill = verde_electo
        fila_actual += 1
    fila_datos_fin = fila_actual - 1

    fila_actual += 1
    if texto_ganador:
        celda = hoja.cell(row=fila_actual, column=1, value=texto_ganador)
        celda.font = Font(bold=True)
        hoja.merge_cells(start_row=fila_actual, start_column=1, end_row=fila_actual, end_column=5)
        celda.alignment = Alignment(wrap_text=True)
        fila_actual += 1

    if texto_corte:
        celda = hoja.cell(row=fila_actual, column=1, value=texto_corte)
        celda.font = Font(bold=True)
        hoja.merge_cells(start_row=fila_actual, start_column=1, end_row=fila_actual, end_column=5)
        celda.alignment = Alignment(wrap_text=True)
        fila_actual += 1

    hoja.column_dimensions['A'].width = 6
    hoja.column_dimensions['B'].width = 42
    hoja.column_dimensions['C'].width = 10
    hoja.column_dimensions['D'].width = 22
    hoja.column_dimensions['E'].width = 10

    if filas:
        grafico = BarChart()
        grafico.title = 'Votos por candidato'
        grafico.y_axis.title = 'Votos'
        grafico.x_axis.title = 'Candidato'
        grafico.style = 10
        grafico.width = 26
        grafico.height = 14

        datos = Reference(hoja, min_col=3, min_row=fila_inicio_tabla, max_row=fila_datos_fin)
        categorias = Reference(hoja, min_col=2, min_row=fila_datos_inicio, max_row=fila_datos_fin)
        grafico.add_data(datos, titles_from_data=True)
        grafico.set_categories(categorias)
        grafico.legend = None

        hoja.add_chart(grafico, f'G{fila_inicio_tabla}')

    libro.save(ruta)
    return ruta


def enviar_resultados_por_correo(asunto, cuerpo):
    """Genera el Excel con los resultados actuales y lo envía por correo al organizador.

    No modifica ningún dato de la votación (papeletas, votos, candidatos):
    solo lee lo que ya existe y arma el reporte.
    """
    if not settings.CORREO_ORGANIZADOR:
        return False

    ruta_excel = generar_excel()
    correo = EmailMessage(
        subject=asunto,
        body=cuerpo,
        from_email=settings.EMAIL_HOST_USER,
        to=[settings.CORREO_ORGANIZADOR],
    )
    correo.attach_file(ruta_excel)
    return bool(correo.send(fail_silently=True))
