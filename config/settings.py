
"""
Django settings for KirayaSetu project.
"""

import os
from pathlib import Path

from dotenv import load_dotenv


# --------------------------------------------------
# BASE DIRECTORY AND ENVIRONMENT VARIABLES
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from backend/.env or root .env
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR.parent / ".env")


def env_bool(name, default=False):
    """Convert environment variable into a boolean."""
    return os.getenv(name, str(default)).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def env_list(name, default=""):
    """Convert comma-separated environment variable into a list."""
    return [
        value.strip()
        for value in os.getenv(name, default).split(",")
        if value.strip()
    ]


# --------------------------------------------------
# SECURITY SETTINGS
# --------------------------------------------------

SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-insecure-k!r@y@-$3tu-default-secret-key-replace-in-production",
)

DEBUG = env_bool("DJANGO_DEBUG", False)

ALLOWED_HOSTS = env_list(
    "DJANGO_ALLOWED_HOSTS",
    "localhost,127.0.0.1",
)
if "testserver" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append("testserver")

# Automatically permit Render domains
render_host = os.getenv("RENDER_EXTERNAL_HOSTNAME")
if render_host and render_host not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(render_host)
if ".onrender.com" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(".onrender.com")


# --------------------------------------------------
# INSTALLED APPLICATIONS
# --------------------------------------------------

INSTALLED_APPS = [
    # Django built-in apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party apps
    "rest_framework",
    "corsheaders",

    # KirayaSetu apps
    "properties",
    "tenants",
    "billing",
    "electricity",
    "payments",
    "dashboard",
    "notifications",
    "accounts",
    "reporting"
]


# --------------------------------------------------
# MIDDLEWARE
# --------------------------------------------------

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# --------------------------------------------------
# URL AND APPLICATION CONFIGURATION
# --------------------------------------------------

ROOT_URLCONF = "config.urls"

WSGI_APPLICATION = "config.wsgi.application"


# --------------------------------------------------
# TEMPLATES
# --------------------------------------------------

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# --------------------------------------------------
# DATABASE CONFIGURATION (PostgreSQL / MySQL / SQLite)
# --------------------------------------------------

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    import dj_database_url
    DATABASES = {
        "default": dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    DB_ENGINE = os.getenv("DB_ENGINE", "mysql").strip().lower()

    if DB_ENGINE in ("sqlite", "sqlite3"):
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": BASE_DIR / os.getenv("SQLITE_DB_NAME", "db.sqlite3"),
            }
        }
    elif DB_ENGINE in ("postgres", "postgresql", "psql"):
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": os.getenv("DB_NAME", "kiraya_db"),
                "USER": os.getenv("DB_USER", "postgres"),
                "PASSWORD": os.getenv("DB_PASSWORD", ""),
                "HOST": os.getenv("DB_HOST", "127.0.0.1"),
                "PORT": os.getenv("DB_PORT", "5432"),
            }
        }
    else:
        db_options = {"charset": "utf8mb4"}
        db_port = os.getenv("DB_PORT", "3306").strip()
        is_ssl_required = (
            env_bool("DB_SSL_REQUIRE", False)
            or bool(os.getenv("DB_SSL_MODE"))
            or db_port == "4000"
        )
        if is_ssl_required:
            ssl_conf = {}
            ca_path = os.getenv("DB_SSL_CA", "").strip()
            if ca_path and os.path.exists(ca_path):
                ssl_conf["ca"] = ca_path
            elif os.path.exists("/etc/ssl/certs/ca-certificates.crt"):
                ssl_conf["ca"] = "/etc/ssl/certs/ca-certificates.crt"
            elif os.path.exists("/etc/ssl/cert.pem"):
                ssl_conf["ca"] = "/etc/ssl/cert.pem"
            db_options["ssl"] = ssl_conf

        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.mysql",
                "NAME": os.getenv("DB_NAME", "kiraya_db"),
                "USER": os.getenv("DB_USER", "root"),
                "PASSWORD": os.getenv("DB_PASSWORD", ""),
                "HOST": os.getenv("DB_HOST", "127.0.0.1"),
                "PORT": db_port,
                "OPTIONS": db_options,
            }
        }


# --------------------------------------------------
# PASSWORD VALIDATION
# --------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]


# --------------------------------------------------
# INTERNATIONALIZATION
# --------------------------------------------------

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Kolkata"

USE_I18N = True

USE_TZ = True


# --------------------------------------------------
# STATIC FILES
# --------------------------------------------------

STATIC_URL = "static/"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/login/"


# --------------------------------------------------
# REACT FRONTEND: CORS AND CSRF
# --------------------------------------------------

_DEFAULT_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://kirayasaathi.app",
    "https://www.kirayasaathi.app",
]

_CONFIGURED_CORS = env_list("CORS_ALLOWED_ORIGINS", "")
CORS_ALLOWED_ORIGINS = list(dict.fromkeys(_DEFAULT_ORIGINS + _CONFIGURED_CORS))

CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://.*\.vercel\.app$",
    r"^https://.*\.onrender\.com$",
    r"^https://.*\.kirayasaathi\.app$",
]

CORS_ALLOW_CREDENTIALS = True

from corsheaders.defaults import default_headers

CORS_ALLOW_HEADERS = list(default_headers) + [
    "x-admin-token",
    "x-auth-token",
]

_CONFIGURED_CSRF = env_list("CSRF_TRUSTED_ORIGINS", "")
CSRF_TRUSTED_ORIGINS = list(dict.fromkeys(
    _DEFAULT_ORIGINS
    + _CONFIGURED_CSRF
    + [
        "https://*.vercel.app",
        "https://*.onrender.com",
        "https://kirayasaathi.app",
        "https://*.kirayasaathi.app",
    ]
))

FRONTEND_URL = os.getenv("FRONTEND_URL", "https://kirayasaathi.app")


# --------------------------------------------------
# SESSION AND COOKIE SECURITY
# --------------------------------------------------

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False

# Cross-domain session support (Vercel frontend + Render backend)
SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "None" if not DEBUG else "Lax")
CSRF_COOKIE_SAMESITE = os.getenv("CSRF_COOKIE_SAMESITE", "None" if not DEBUG else "Lax")

# HTTPS-only cookies in production (Required when SameSite is None)
SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", not DEBUG)
CSRF_COOKIE_SECURE = env_bool("CSRF_COOKIE_SECURE", not DEBUG)


# --------------------------------------------------
# ADDITIONAL SECURITY HEADERS
# --------------------------------------------------

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"


# --------------------------------------------------
# DJANGO REST FRAMEWORK
# --------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "accounts.authentication.CsrfExemptSessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "accounts.permissions.IsVerifiedOwner",
    ],
}


# --------------------------------------------------
# PRODUCTION HTTPS SETTINGS
# --------------------------------------------------
# These activate when DEBUG=False.
# Production deployment must have HTTPS correctly configured.

# Reverse proxy SSL header (Critical for Render, Heroku, Nginx HTTPS detection)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = not DEBUG

SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0

SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG

SECURE_HSTS_PRELOAD = False


# --------------------------------------------------
# NOTIFICATION & MESSAGING SERVICE SETTINGS
# --------------------------------------------------

# Ensure SSL certificate bundle is available on macOS/Linux for SMTP TLS
if "SSL_CERT_FILE" not in os.environ:
    for _cert_path in ["/etc/ssl/certs/ca-certificates.crt", "/etc/ssl/cert.pem", "/etc/pki/tls/cert.pem"]:
        if os.path.exists(_cert_path):
            os.environ["SSL_CERT_FILE"] = _cert_path
            break

EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "kirayasaathi.support@gmail.com").strip()
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "tvlybnzksxcbxbdf").replace(" ", "").strip()
EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND",
    "django.core.mail.backends.smtp.EmailBackend"
    if EMAIL_HOST_USER
    else "django.core.mail.backends.console.EmailBackend",
)
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
EMAIL_TIMEOUT = int(os.getenv("EMAIL_TIMEOUT", 10))

BREVO_API_KEY = os.getenv("BREVO_API_KEY", "").strip()
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "").strip()
_default_from = (
    f"KirayaSaathi <{EMAIL_HOST_USER}>"
    if (BREVO_API_KEY or EMAIL_HOST_USER)
    else ("KirayaSaathi <onboarding@resend.dev>" if RESEND_API_KEY else "KirayaSaathi <kirayasaathi.support@gmail.com>")
)
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", _default_from)
ALLOW_OTP_FALLBACK = env_bool("ALLOW_OTP_FALLBACK", True)

# SMS & WhatsApp Gateway Configuration (Twilio, Fast2SMS, Meta WhatsApp API)
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "")
SMS_API_KEY = os.getenv("SMS_API_KEY", "")
FAST2SMS_API_KEY = os.getenv("FAST2SMS_API_KEY", SMS_API_KEY).strip()
WHATSAPP_API_TOKEN = os.getenv("WHATSAPP_API_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")


# --------------------------------------------------
# DEFAULT PRIMARY KEY
# --------------------------------------------------

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
