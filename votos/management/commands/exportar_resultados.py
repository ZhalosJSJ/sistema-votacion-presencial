import csv

from django.core.management.base import BaseCommand

from votos.reportes import calcular_resumen, generar_excel


class Command(BaseCommand):
    help = (
        'Exporta un resumen de la votación (participantes, resultados por candidato y '
        'directorio electo) a resultados_votacion.csv y resultados_votacion.xlsx'
    )

    def handle(self, *args, **options):
        filas, total_participantes, texto_ganador, texto_corte = calcular_resumen()

        with open('resultados_votacion.csv', 'w', newline='', encoding='utf-8') as archivo:
            escritor = csv.writer(archivo)
            escritor.writerow(['N°', 'Candidato', 'Votos', '% del total de votos', 'Electo'])
            for fila in filas:
                escritor.writerow([
                    fila['numero'],
                    fila['nombre'],
                    fila['votos'],
                    f"{fila['porcentaje']:.2f}%",
                    'Sí' if fila['electo'] else '',
                ])
            escritor.writerow([])
            escritor.writerow(['Participantes que votaron', total_participantes])

        generar_excel()

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=== Resumen de votación ==='))
        self.stdout.write(f'Participantes que votaron: {total_participantes}')
        self.stdout.write('')
        self.stdout.write('Resultados por candidato:')
        for fila in filas:
            marca = ' [ELECTO]' if fila['electo'] else ''
            self.stdout.write(f"  N°{fila['numero']} {fila['nombre']}: {fila['votos']} votos ({fila['porcentaje']:.2f}%){marca}")

        if texto_ganador:
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS(texto_ganador))
        if texto_corte:
            self.stdout.write(self.style.SUCCESS(texto_corte))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            'Se guardó el detalle en resultados_votacion.csv y resultados_votacion.xlsx'
        ))
