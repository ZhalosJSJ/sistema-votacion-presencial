"""
Configuración del proyecto de votación.
Los valores sensibles (contraseñas, correos) se leen desde el archivo .env
para que nunca queden escritos directamente en el código.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Carga las variables de .env al entorno si aún no están definidas.
# Docker ya las inyecta vía "env_file", pero al correr la app directamente
# (fuera de Docker) hay que leer el archivo aquí para que no queden vacías.
_env_path = BASE_DIR / '.env'
if _env_path.exists():
    for _linea in _env_path.read_text().splitlines():
        _linea = _linea.strip()
        if not _linea or _linea.startswith('#') or '=' not in _linea:
            continue
        _clave, _valor = _linea.split('=', 1)
        os.environ.setdefault(_clave.strip(), _valor.strip())

# --- Seguridad básica ---
SECRET_KEY = os.environ.get('SECRET_KEY', 'clave-de-desarrollo-cambiar-en-produccion')
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

# '*' permite que cualquier dispositivo en la red local se conecte.
# Esto es aceptable porque la app solo corre en tu red WiFi local, no en internet.
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'votos',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'votacion.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'votacion.wsgi.application'

# --- Base de datos: sqlite, un solo archivo local, simple para este caso ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Configuración de correo (para avisar cuando llega un voto) ---
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')

# Correo (o correos) donde quieres recibir el aviso de cada voto
CORREO_ORGANIZADOR = os.environ.get('CORREO_ORGANIZADOR', '')

# --- Personalización de la votación ---
# Permiten reutilizar la app en cualquier elección sin tocar el código:
# se definen en el .env y se usan en la pantalla de resultados y en el Excel.

# Título que encabeza la pantalla de resultados en vivo y el reporte.
VOTACION_TITULO = os.environ.get('VOTACION_TITULO', 'Elección de Directorio')

# Texto que acompaña a los electos al cerrar la votación.
VOTACION_SUBTITULO_ELECTOS = os.environ.get('VOTACION_SUBTITULO_ELECTOS', 'Directorio electo')

# Logo que se muestra en la esquina de la pantalla de resultados.
# Es una ruta relativa dentro de static/. Déjalo vacío para no mostrar ninguno.
ORGANIZACION_LOGO = os.environ.get('ORGANIZACION_LOGO', 'logo.svg')

# Texto alternativo del logo (accesibilidad). Debe corresponder al logo que
# esté configurado en ORGANIZACION_LOGO.
ORGANIZACION_NOMBRE = os.environ.get('ORGANIZACION_NOMBRE', 'ProyectsZH')
