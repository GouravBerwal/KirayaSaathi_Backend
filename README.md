# KirayaSetu Django Backend

Django REST Framework backend for rental properties, rooms, tenants, rental agreements, rent records, electricity metering/billing, payments, dashboards, and owner notifications.

## React integration

Read [`api.md`](api.md) first. It is the current endpoint contract, including session/CSRF, request examples, response examples, and owner-scoping behavior.

## Local setup

1. Use Python 3.14.x (the project was developed with Django 6.1.2).
2. Create and activate a virtual environment.
3. Install dependencies: `python -m pip install -r requirements.txt`.
4. Copy `.env.example` to `.env` and configure a new local secret key and MySQL credentials.
5. Ensure the MySQL database exists and the configured user has access.
6. Back up any existing database before applying migrations.
7. Run `python manage.py migrate`, then `python manage.py check`.
8. Run `python manage.py runserver` for local development.

Do not copy a developer's `.env`, session cookies, local database, or virtual environment into a delivery package.

## Tests

Run `./scripts/check_backend.sh`. This script switches to `config.test_settings` and uses an in-memory SQLite test database, so the automated tests do not touch your configured MySQL data. Never point tests at production data.

## Existing-data migration

The ownership migrations preserve existing business columns and records. Existing properties are assigned to the confirmed `gurjar` owner. Existing tenant ownership is derived from rental agreements. Tenants without agreements remain unassigned rather than having their owner guessed; these are visible to administrators so their ownership can be explicitly mapped.

## Security notes

- Every business endpoint requires authentication.
- Querysets and relationship validation enforce owner boundaries.
- Browser clients must include cookies and send the CSRF header for unsafe methods.
- Use HTTPS and `DJANGO_DEBUG=False` in production.
