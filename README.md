# Sistema de Votación Presencial

Aplicación web en Django para llevar el conteo de una elección presencial —
por ejemplo, la renovación de un directorio en una asamblea de ~100 personas —
desde el computador del organizador, sin depender de internet.

Fue construida para una elección real de directorio con 7 cupos y 14
candidatos, y usada en producción durante el evento.

---

## 1. Cómo funciona

No es un sistema de autoservicio: **un solo operador** registra los votos a
medida que cada participante anuncia sus elecciones. Esto evita tener que
repartir dispositivos, instalar nada en los teléfonos o depender de la WiFi
del lugar.

1. Cada candidato tiene un número fijo (campo `orden`, único).
2. El participante dice a quiénes elige; el operador escribe esos números
   separados por espacio o coma (ej. `3 7 11 2`).
3. Los votos se guardan juntos como una **papeleta** — un registro por
   participante, con sus votos asociados.
4. Una pantalla de **resultados en vivo** se proyecta en la sala y se
   actualiza sola cada 3 segundos.
5. Al cerrar la votación, el sistema envía por correo un Excel con el
   resumen final: participantes, votos y porcentaje por candidato,
   el directorio electo y un gráfico de barras.

Cada participante puede elegir entre 1 y 7 candidatos
(`MAX_VOTOS_POR_PAPELETA` en `votos/models.py`), sin repetir.

> **Sobre el anonimato:** el sistema no está diseñado para ser anónimo. Es
> el propio operador quien ingresa los votos, así que no hay separación
> entre quién emite el voto y por quién vota. Si necesitas una votación
> secreta, este no es el diseño adecuado.

---

## 2. Pantallas

| Ruta | Para qué sirve | Acceso |
|---|---|---|
| `/` | Registrar papeletas (pantalla del operador) | Abierta |
| `/resultados-en-vivo/` | Conteo en vivo, para proyectar | Abierta |
| `/resultados-en-vivo/datos/` | Endpoint JSON que alimenta la pantalla anterior | Abierta |
| `/admin/` | Cargar candidatos, fotos y descripciones | Staff |
| `/organizador/cerrar-votacion/` | Cierra la votación y envía el Excel por correo | Staff |
| `/organizador/reiniciar-votacion/` | Borra todas las papeletas (pide confirmación) | Staff |

Al cerrar la votación, la pantalla de resultados en vivo pasa a mostrar las
fotos de los electos en lugar del conteo en progreso.

---

## 3. Instalación

### 3.1 Configuración

Copia `.env.example` a `.env` y completa los valores:

```bash
cp .env.example .env
```

| Variable | Qué es |
|---|---|
| `SECRET_KEY` | Cualquier texto largo y aleatorio |
| `DEBUG` | `True` para uso local |
| `EMAIL_HOST_USER` | Cuenta de Gmail que envía los avisos |
| `EMAIL_HOST_PASSWORD` | **Contraseña de aplicación** de Gmail, de 16 caracteres (no la contraseña normal de la cuenta) |
| `CORREO_ORGANIZADOR` | Correo donde llegan los resultados |

La contraseña de aplicación se crea en: Cuenta de Google → Seguridad →
Verificación en 2 pasos → Contraseñas de aplicaciones. Para usar otro
proveedor SMTP, ajusta `EMAIL_HOST` y `EMAIL_PORT` en `votacion/settings.py`.

### 3.1.1 Personalizar la votación (opcional)

Los textos y el logo no están escritos en el código: salen del `.env`, así
que la app se reutiliza en cualquier elección sin tocar los archivos fuente.

| Variable | Por defecto | Qué controla |
|---|---|---|
| `VOTACION_TITULO` | `Elección de Directorio` | Encabezado de la pantalla de resultados y título del Excel |
| `VOTACION_SUBTITULO_ELECTOS` | `Directorio electo` | Texto sobre las fotos de los electos al cerrar |
| `ORGANIZACION_LOGO` | `logo.svg` | Ruta del logo dentro de `static/`. Vacío = sin logo |
| `ORGANIZACION_NOMBRE` | `ProyectsZH` | Texto alternativo del logo |

Para usar tu propia marca, reemplaza `static/logo.svg` o apunta
`ORGANIZACION_LOGO` a otro archivo dentro de `static/`, y ajusta
`ORGANIZACION_NOMBRE` para que el texto alternativo coincida.

### 3.2 Con Docker

```bash
docker compose up --build
```

```bash
docker compose exec web python manage.py migrate
```

```bash
docker compose exec web python manage.py createsuperuser
```

### 3.3 Sin Docker

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

```bash
.venv/bin/python manage.py migrate && .venv/bin/python manage.py createsuperuser
```

```bash
.venv/bin/python manage.py runserver 0.0.0.0:8000
```

`settings.py` carga el `.env` por su cuenta, así que ambos flujos funcionan
igual.

---

## 4. Antes del evento

1. Entra a `/admin/` y crea los candidatos. A cada uno asígnale **nombre**,
   **descripción**, **foto** y un **número de orden único** — ese número es
   el que el operador teclea para votar.
2. Las fotos se guardan en `media/candidatos/`. Esa carpeta no está en el
   repositorio: contiene datos personales y se llena desde el panel de
   administración.
3. Haz una prueba completa: registra 2 o 3 papeletas, revisa la pantalla de
   resultados, cierra la votación y confirma que el correo llega. Después
   usa `/organizador/reiniciar-votacion/` para dejar el conteo en cero.

### Proyectar los resultados desde otro dispositivo

```bash
.venv/bin/python generar_qr.py <IP_LOCAL>
```

Genera un QR con la URL de resultados en vivo. La IP local se obtiene con
`hostname -I`; el otro dispositivo debe estar en la misma red.

---

## 5. Exportar resultados sin cerrar la votación

```bash
.venv/bin/python manage.py exportar_resultados
```

Genera `resultados_votacion.csv` y `resultados_votacion.xlsx` con el estado
actual del conteo y lo envía por correo, sin modificar ningún dato.

---

## 6. Arquitectura

```
votacion/          Configuración del proyecto (settings, urls raíz, wsgi)
votos/             Única app: toda la lógica
  models.py        Candidato, Papeleta, Voto, EstadoVotacion
  views.py         Registro de papeletas, resultados en vivo, cierre, reinicio
  reportes.py      Cálculo del resumen, generación del Excel y envío por correo
  templates/       Pantallas del operador y de resultados
  management/      Comando exportar_resultados
templates/admin/   Portada del admin con accesos directos a las pantallas
static/            Logo e imágenes de la interfaz
generar_qr.py      Script independiente para generar el QR de resultados
```

Los modelos: `Candidato` (nombre, descripción, foto, `orden` único),
`Papeleta` (un participante, solo marca de tiempo), `Voto` (FK a papeleta y
a candidato) y `EstadoVotacion` (singleton que indica si ya se cerró).

`CUPOS_DIRECTORIO = 7` en `votos/models.py` define cuántos candidatos
quedan marcados como electos en el reporte.

---

## 7. Limitaciones conocidas

- `ALLOWED_HOSTS = ['*']` y `DEBUG=True` por defecto. Es intencional para
  una red local confiable durante un evento — **no está pensado para
  exponerse a internet** sin ajustar ambos valores.
- Base de datos SQLite, suficiente para la escala de un evento presencial.
- Sin suite de pruebas automatizadas.
- El envío de correo usa `fail_silently=True`: si el SMTP falla, la votación
  continúa sin interrumpirse, pero el aviso no llega.

---

## 8. Stack

Django 5.0 · SQLite · Pillow · openpyxl · qrcode · Docker
