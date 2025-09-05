from .base import *

DEBUG = True
ALLOWED_HOSTS = ["*"]  # pratique pour LAN, sinon limite à 127.0.0.1/localhost

# CORS: en dev, tout ouvert
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = ["http://192.168.1.121:8081"]

# Emails affichés dans la console
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Ajoute django_extensions en dev seulement
INSTALLED_APPS += ["django_extensions"]
