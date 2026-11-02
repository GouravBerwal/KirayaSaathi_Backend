from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def assign_existing_properties_to_confirmed_owner(apps, schema_editor):
    Property = apps.get_model("properties", "Property")
    User = apps.get_model(*settings.AUTH_USER_MODEL.split("."))
    database = schema_editor.connection.alias

    if not Property.objects.using(database).exists():
        return

    # This mapping was explicitly confirmed for the existing deployment:
    # both current properties belong to username "gurjar" (User ID 1).
    owner = User.objects.using(database).filter(username="gurjar").first()
    if owner is None:
        raise RuntimeError(
            "Cannot migrate existing properties: the confirmed owner "
            "'gurjar' was not found. No ownership mapping was guessed."
        )

    Property.objects.using(database).filter(owner__isnull=True).update(
        owner_id=owner.pk
    )


def reverse_property_owner_mapping(apps, schema_editor):
    Property = apps.get_model("properties", "Property")
    database = schema_editor.connection.alias
    Property.objects.using(database).update(owner_id=None)


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("properties", "0002_room"),
    ]

    operations = [
        migrations.AddField(
            model_name="property",
            name="owner",
            field=models.ForeignKey(
                to=settings.AUTH_USER_MODEL,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="owned_properties",
                null=True,
            ),
        ),
        migrations.RunPython(
            assign_existing_properties_to_confirmed_owner,
            reverse_property_owner_mapping,
        ),
        migrations.AlterField(
            model_name="property",
            name="owner",
            field=models.ForeignKey(
                to=settings.AUTH_USER_MODEL,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="owned_properties",
            ),
        ),
    ]
