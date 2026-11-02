# Existing Database Migration Notes

These migrations add owner associations; they do not drop or rename existing business fields or tables.

## Before migrating the existing MySQL database

Create a backup first. For the current local connection values, run this in Terminal and enter the MySQL password when prompted:

```bash
mysqldump -h 127.0.0.1 -P 3306 -u root -p kiraya_db > kiraya_db_backup_$(date +%Y%m%d_%H%M%S).sql
```

Verify the backup file exists and is non-empty before continuing.

## What the migrations do

1. `properties.0003_property_owner` adds `Property.owner` and assigns the existing property records to the confirmed `gurjar` owner account. This account and mapping were verified from the current project's read-only output (two properties, both mapped to User ID 1).
2. `tenants.0003_tenant_owner` adds nullable `Tenant.owner`. Tenants with existing rental agreements inherit the owner of their agreement's property. Tenants without agreements remain unassigned rather than having their owner guessed.
3. `electricity.0002_unique_bill_reading` enforces one electricity bill per meter reading to prevent duplicate generated bills.

No existing business field is deleted or renamed. The migrations do not clear tables and do not reset the database.

## Apply the migrations

Run from the `backend` directory with the project's virtual environment active:

```bash
python manage.py check
python manage.py migrate --plan
python manage.py migrate
python manage.py check
```

Do **not** run `flush`, delete `db.sqlite3`, drop tables, or reset the MySQL database.

## Legacy tenants without agreements

Such records have `owner = NULL` after migration and are deliberately excluded from normal owner-scoped API responses. A staff administrator can open Django Admin → Tenants, filter Owner to the blank option, and use the editable Owner column to assign them explicitly. This avoids incorrectly assigning personal data to the wrong account.
