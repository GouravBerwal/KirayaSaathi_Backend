from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def assign_tenants_from_existing_agreements(apps, schema_editor):
    Tenant = apps.get_model("tenants", "Tenant")
    RentalAgreement = apps.get_model("tenants", "RentalAgreement")
    database = schema_editor.connection.alias

    for tenant in Tenant.objects.using(database).all().iterator():
        owners = set(
            RentalAgreement.objects.using(database)
            .filter(tenant_id=tenant.pk)
            .values_list("room__property__owner_id", flat=True)
            .distinct()
        )
        owners.discard(None)

        if len(owners) > 1:
            raise RuntimeError(
                f"Tenant ID {tenant.pk} has agreements associated with "
                "multiple owners. Resolve the data inconsistency before "
                "applying owner isolation."
            )

        if len(owners) == 1:
            Tenant.objects.using(database).filter(pk=tenant.pk).update(
                owner_id=next(iter(owners))
            )
        # A tenant without any agreement is intentionally left unassigned;
        # assigning it to an owner without evidence could expose personal data.


def reverse_tenant_owner_mapping(apps, schema_editor):
    Tenant = apps.get_model("tenants", "Tenant")
    database = schema_editor.connection.alias
    Tenant.objects.using(database).update(owner_id=None)


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("properties", "0003_property_owner"),
        ("tenants", "0002_rentalagreement"),
    ]

    operations = [
        migrations.AddField(
            model_name="tenant",
            name="owner",
            field=models.ForeignKey(
                to=settings.AUTH_USER_MODEL,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="owned_tenants",
                null=True,
                blank=True,
            ),
        ),
        migrations.RunPython(
            assign_tenants_from_existing_agreements,
            reverse_tenant_owner_mapping,
        ),
    ]
