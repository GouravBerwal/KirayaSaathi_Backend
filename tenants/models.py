
from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError


class Tenant(models.Model):
    # Nullable only for legacy tenants that have no agreement to establish
    # their owner safely. New API-created tenants always get an owner.
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_tenants",
        null=True,
        blank=True,
    )

    full_name = models.CharField(max_length=150)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=15)
    alternate_phone = models.CharField(max_length=15, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    occupation = models.CharField(max_length=150, blank=True, default="")
    emergency_contact_name = models.CharField(
        max_length=150,
        blank=True,
    )
    emergency_contact_relationship = models.CharField(
        max_length=80,
        blank=True,
        default="",
    )
    emergency_contact_phone = models.CharField(
        max_length=15,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.full_name


class RentalAgreement(models.Model):
    AGREEMENT_STATUSES = [
        ("ACTIVE", "Active"),
        ("COMPLETED", "Completed"),
        ("TERMINATED", "Terminated"),
    ]

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.PROTECT,
        related_name="agreements",
    )

    room = models.ForeignKey(
        "properties.Room",
        on_delete=models.PROTECT,
        related_name="rental_agreements",
    )

    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    monthly_rent = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    security_deposit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    SECURITY_DEPOSIT_STATUSES = [
        ("PENDING", "Pending"),
        ("PAID", "Paid"),
        ("REFUNDED", "Refunded"),
        ("SETTLED", "Partially Settled"),
    ]

    security_deposit_status = models.CharField(
        max_length=20,
        choices=SECURITY_DEPOSIT_STATUSES,
        default="PENDING",
    )

    deposit_paid_date = models.DateField(null=True, blank=True)
    deposit_refund_date = models.DateField(null=True, blank=True)
    deposit_payment_method = models.CharField(max_length=30, blank=True, default="UPI")
    deposit_transaction_ref = models.CharField(max_length=100, blank=True, default="")

    refund_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    deduction_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    deduction_reason = models.TextField(blank=True, default="")
    handover_items = models.JSONField(default=list, blank=True)
    handover_notes = models.TextField(blank=True, default="")

    status = models.CharField(
        max_length=20,
        choices=AGREEMENT_STATUSES,
        default="ACTIVE",
    )

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        super().clean()

        # Tenant and room must always belong to the same owner, including
        # completed/terminated agreements.
        if self.tenant_id and self.room_id:
            tenant_owner_id = self.tenant.owner_id
            room_owner_id = self.room.property.owner_id
            if tenant_owner_id is None or tenant_owner_id != room_owner_id:
                raise ValidationError({
                    "tenant": "Tenant and room must belong to the same owner."
                })

        if not self.room_id or self.status != "ACTIVE":
            return

        # Check room maintenance status
        if self.room.status == "MAINTENANCE":
            raise ValidationError({
                "room": "A room under maintenance cannot be assigned."
            })

        # Check whether room capacity has been reached
        capacity = getattr(self.room, "capacity", 1)
        active_agreements = RentalAgreement.objects.filter(
            room_id=self.room_id,
            status="ACTIVE",
        )
        if self.pk:
            active_agreements = active_agreements.exclude(pk=self.pk)

        if active_agreements.count() >= capacity:
            room_type_name = self.room.get_room_type_display() if hasattr(self.room, "get_room_type_display") else self.room.room_type
            raise ValidationError({
                "room": f"Room {self.room.room_number} ({room_type_name}) already has {active_agreements.count()} active tenant(s) and has reached its maximum capacity of {capacity} tenant(s)."
            })

    def __str__(self):
        return (
            f"{self.tenant.full_name} - "
            f"Room {self.room.room_number}"
        )
