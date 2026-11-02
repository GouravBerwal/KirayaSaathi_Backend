"""Settings for an isolated local test run; never use for deployment."""

import os

# Allow source checks/tests to run without requiring real deployment secrets.
# These values are test-only and are never used by the normal settings module.
os.environ.setdefault("DJANGO_SECRET_KEY", "test-only-key-not-for-deployment")
os.environ.setdefault("DB_PASSWORD", "")

from .settings import *  # noqa: E402,F403

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
