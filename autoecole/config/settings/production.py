from .base import *

DEBUG = False

# Clés/hosts obligatoires en prod
SECRET_KEY = env("SECRET_KEY")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")  # ex: monsite.com,www.monsite.com

# Si Django est derrière Nginx/Traefik/ALB en HTTPS
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# CORS / CSRF (front séparé)
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

# Cookies & sécurité HTTP
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=False)  # True si HTTPS partout
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=0)       # 31536000 une fois HTTPS OK
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = False
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# Logging un poil plus verbeux en prod
LOGGING["root"]["level"] = env("DJANGO_LOG_LEVEL", default="INFO")

# Optionnel : admin non trivial
ADMIN_URL = env("ADMIN_URL", default="admin/")

# (DB: déjà gérée par base.py via DATABASE_URL)
