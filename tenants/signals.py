from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver

from properties.models import Room
from .models import RentalAgreement


def sync_room_occupancy(room_id):
    if room_id is None:
        return

    try:
        room = Room.objects.get(pk=room_id)
    except Room.DoesNotExist:
        return

    # Maintenance status ko kabhi automatically change nahi karna
    if room.status == "MAINTENANCE":
        return

    has_active_agreement = RentalAgreement.objects.filter(
        room_id=room_id,
        status="ACTIVE"
    ).exists()

    new_status = "OCCUPIED" if has_active_agreement else "VACANT"

    if room.status != new_status:
        room.status = new_status
        room.save(update_fields=["status", "updated_at"])


@receiver(pre_save, sender=RentalAgreement)
def remember_previous_room(sender, instance, **kwargs):
    if instance.pk:
        instance._previous_room_id = (
            RentalAgreement.objects
            .filter(pk=instance.pk)
            .values_list("room_id", flat=True)
            .first()
        )
    else:
        instance._previous_room_id = None


@receiver(post_save, sender=RentalAgreement)
def update_room_after_agreement_save(
    sender, instance, created, **kwargs
):
    previous_room_id = getattr(
        instance, "_previous_room_id", None
    )

    room_ids = {
        instance.room_id,
        previous_room_id,
    }

    for room_id in room_ids:
        sync_room_occupancy(room_id)


@receiver(post_delete, sender=RentalAgreement)
def update_room_after_agreement_delete(
    sender, instance, **kwargs
):
    sync_room_occupancy(instance.room_id)