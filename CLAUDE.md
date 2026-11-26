# CLAUDE.md

Este archivo entrega contexto a Claude Code (claude.ai/code) para trabajar en el código de este repositorio.

## Descripción del proyecto

Una aplicación Django mínima para llevar el conteo de una votación presencial (por ejemplo, una elección en un evento de ~100 personas) desde el computador del organizador. **No es un sistema de autoservicio para los votantes**: un solo operador va sentado frente al computador y registra los votos a medida que cada participante anuncia sus elecciones — no requiere WiFi, conexión celular ni que cada votante tenga su propio dispositivo. Cada participante elige entre 1 y `MAX_VOTOS_POR_PAPELETA` (7) candidatos de una lista numerada; el operador escribe esos números y se registran todos juntos como una "papeleta". Hay una pantalla de resultados en vivo pensada para proyectar mientras se van ingresando los votos, y un botón para cerrar la votación y enviar por correo un Excel con el resumen final. El sistema **no es anónimo** (a diferencia de una versión anterior de este proyecto basada en códigos de un solo uso): no hay necesidad de desvincular el voto de quién lo emite, porque es el propio operador quien lo ingresa. Todo el texto de la interfaz, las plantillas y los comentarios del código están en español (locale es-cl); mantén los nuevos textos visibles y comentarios en español para conservar la consistencia.

## Comandos

La app corre dentro de Docker (`docker-compose.yml`), pero también se puede correr directo con un entorno virtual de Python si Docker no está disponible.

```bash
docker compose up --build          # construye la imagen y levanta el servidor en :8000
docker compose up                  # levanta la app (si ya está construida)
docker compose down                # detiene la app
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py exportar_resultados     # genera resultados_votacion.csv y .xlsx
docker compose exec web python generar_qr.py <IP_LOCAL>          # genera qr_votacion.png (útil solo si se quiere ver la pantalla de resultados en vivo desde otro dispositivo en la red)
```

Sin Docker (entorno virtual local):

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver 0.0.0.0:8000
```

`settings.py` carga las variables de `.env` por sí mismo (no depende únicamente de `env_file` de Docker), así que ambos flujos funcionan igual.

No existe suite de pruebas en este repositorio (no hay `tests.py` ni configuración de pytest). Si se agregan pruebas, deben ejecutarse con `docker compose exec web python manage.py test` (o `.venv/bin/python manage.py test`).

## Arquitectura

Estructura estándar de Django con dos paquetes:

- `votacion/` — configuración del proyecto: `settings.py`, `urls.py` raíz, `wsgi.py`. Lee los valores sensibles (`SECRET_KEY`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `CORREO_ORGANIZADOR`, `DEBUG`) desde variables de entorno, cargando `.env` manualmente al inicio de `settings.py` si existe (para que funcione tanto dentro como fuera de Docker). `ALLOWED_HOSTS = ['*']` y `DEBUG=True` por defecto — es intencional para un evento de red local confiable, no está pensado para exponerse a internet. `TEMPLATES.DIRS` incluye `templates/` a nivel de proyecto (se usa para sobrescribir `admin/index.html`, ver más abajo).
- `votos/` — la única app, contiene toda la lógica:
  - `models.py` — define `MAX_VOTOS_POR_PAPELETA = 7` y tres modelos: `Candidato` (nombre/descripción/foto/`orden`, donde `orden` es único y funciona como el número que el operador escribe para elegirlo), `Papeleta` (una ronda de votación = un participante, solo tiene `fecha_hora`), `Voto` (FK a `Papeleta` y a `Candidato` — un `Voto` por cada candidato elegido dentro de una papeleta).
  - `views.py`:
    - `registrar_voto` (`/`) — pantalla del operador. Recibe un texto con entre 1 y `MAX_VOTOS_POR_PAPELETA` números separados por espacio/coma, sin repetidos, que correspondan a candidatos existentes (`Candidato.orden`); si todo es válido crea una `Papeleta` y sus `Voto` en bloque (`bulk_create`) y limpia el formulario para seguir cargando la siguiente papeleta. Muestra el conteo de participantes registrados.
    - `reiniciar_votacion` (`/organizador/reiniciar-votacion/`, protegida con `@staff_member_required`) — borra TODAS las papeletas/votos (no los candidatos). Requiere escribir la palabra `REINICIAR` en el formulario para confirmar, porque no se puede deshacer.
    - `resultados_en_vivo` (`/resultados-en-vivo/`) — página pensada para proyectar; hace `fetch()` cada 3 segundos a `resultados_en_vivo_datos` (JS inline, sin dependencias).
    - `resultados_en_vivo_datos` (`/resultados-en-vivo/datos/`) — endpoint JSON con el conteo actual por candidato (usa `votos/reportes.py::calcular_resumen`).
    - `cerrar_votacion` (`/organizador/cerrar-votacion/`, protegida con `@staff_member_required`) — botón manual que llama a `enviar_resultados_por_correo` sin tocar ni borrar ninguna papeleta/voto; se puede usar varias veces.
  - `reportes.py` — lógica compartida de reportes: `calcular_resumen()` (participantes = `Papeleta.objects.count()`, votos y % por candidato sobre el total de participantes), `generar_excel()` (arma `resultados_votacion.xlsx` con `openpyxl`), `enviar_resultados_por_correo()` (genera el Excel y lo manda por correo, `fail_silently=True`, usado tanto por `cerrar_votacion` como por el comando `exportar_resultados`).
  - `urls.py` — namespace `votos` (`/`, `/resultados-en-vivo/`, `/resultados-en-vivo/datos/`, `/organizador/cerrar-votacion/`).
  - `templates/votos/` — `registrar_voto.html`, `resultados_en_vivo.html`, `cerrar_votacion.html`.
  - `management/commands/exportar_resultados.py` — genera `resultados_votacion.csv` y `.xlsx` con el resumen actual (usa `votos/reportes.py`).
  - `admin.py` — registra `Candidato`, `Papeleta` y `Voto` como panel de control del organizador.
- `templates/admin/index.html` — sobrescribe la portada del admin de Django (copia completa de la plantilla original, **no usa `{% extends "admin/index.html" %}`** porque causaría un loop de recursión) para agregar accesos directos a "Registrar votos", "Resultados en vivo" y "Cerrar votación ahora". Requiere que `templates/` esté en `TEMPLATES.DIRS` en `settings.py`.
- `generar_qr.py` — script independiente (se ejecuta con `python`, no con `manage.py`) que recibe una IP y genera `qr_votacion.png`; ya no es parte del flujo principal de votación (el operador usa el computador directamente), pero sirve para compartir la URL de `resultados-en-vivo` si se quiere ver desde otro dispositivo en la red.

### Puntos clave a tener en cuenta al modificar código

- El voto **ya no es anónimo**: `Voto` tiene FK directa a `Papeleta`. No hay que preservar ninguna separación entre "quién ingresó el voto" y "por quién votó" (a diferencia de una versión anterior de este proyecto).
- `Candidato.orden` es único y cumple doble función: orden de despliegue y número que el operador teclea en `registrar_voto`. Si se agregan candidatos nuevos desde el admin, hay que asignarles un `orden` que no choque con los existentes (el campo ya no tiene `default=0`, así que el admin exige completarlo).
- `MAX_VOTOS_POR_PAPELETA` (en `models.py`) es la única fuente de verdad del máximo de candidatos por participante (mínimo siempre es 1) — se usa tanto en la validación de `registrar_voto` como en el template.
- **No escribas textos de marca ni nombres de organizaciones en el código.** El título de la votación, el subtítulo de los electos y el logo salen de variables de entorno (`VOTACION_TITULO`, `VOTACION_SUBTITULO_ELECTOS`, `ORGANIZACION_LOGO`, `ORGANIZACION_NOMBRE`), definidas en `settings.py` con valores genéricos por defecto. `resultados_en_vivo` las pasa al template y `reportes.py` usa `settings.VOTACION_TITULO` para el encabezado del Excel. Si se agrega una pantalla nueva que muestre la marca, hay que pasar esas variables al contexto en vez de hardcodearlas.
- `static/logo.svg` es un marcador de posición pensado para reemplazarse. Las fotos de candidatos viven en `media/`, que está fuera del repositorio porque son datos personales: se cargan desde el panel de administración.
