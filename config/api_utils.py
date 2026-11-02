"""Small API helpers shared across resource views."""

from django.db.models.deletion import ProtectedError
from rest_framework.exceptions import ValidationError


def safe_delete(instance):
    """Turn protected related-row deletes into a documented 400 response."""
    try:
        instance.delete()
    except ProtectedError as exc:
        raise ValidationError({
            "detail": (
                "This record cannot be deleted while related rental, bill, "
                "or payment records depend on it. Resolve those records first."
            )
        }) from exc
