from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import OwnerProfile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_owner_profile_for_new_user(sender, instance, created, **kwargs):
    """
    Ensure each user has an OwnerProfile.
    Direct ORM/admin creations default to verified and approved so existing unit tests and
    fixtures continue to work as expected. Public registration explicitly sets unverified/pending.
    """
    if created:
        default_verified = getattr(instance, "_default_verified", True)
        default_approval = getattr(
            instance,
            "_default_approval",
            "APPROVED" if default_verified else "NOT_SUBMITTED",
        )
        default_access = getattr(instance, "_default_access", "ACTIVE")

        OwnerProfile.objects.get_or_create(
            user=instance,
            defaults={
                "email_verified": default_verified,
                "approval_status": default_approval,
                "access_status": default_access,
            },
        )
