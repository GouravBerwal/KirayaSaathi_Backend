#!/bin/sh
set -eu

# Run fast checks/tests against an isolated in-memory SQLite test database.
# This script does not migrate or write to the configured MySQL database.
export DJANGO_SETTINGS_MODULE=config.test_settings
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test --verbosity 2
