
from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError


class Notification(models.Model):

    NOTIFICATION_TYPES = [
        ("RENT_UPCOMING", "Upcoming Rent Due"),
        ("RENT_OVERDUE", "Overdue Rent"),
        ("ELECTRICITY_UPCOMING", "Upcoming Electricity Bill"),
        ("ELECTRICITY_OVERDUE", "Overdue Electricity Bill"),
    ]

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    rent_record = models.ForeignKey(
        "billing.RentRecord",
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True,
    )

    electricity_bill = models.ForeignKey(
        "electricity.ElectricityBill",
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True,
    )

    notification_type = models.CharField(
        max_length=30,
        choices=NOTIFICATION_TYPES,
    )

    title = models.CharField(max_length=200)

    message = models.TextField()

    due_date = models.DateField()

    amount_due = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    is_read = models.BooleanField(default=False)

    read_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    is_sent = models.BooleanField(default=False)

    sent_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    sent_via = models.CharField(
        max_length=50,
        blank=True,
        default="",
    )

    delivery_status = models.CharField(
        max_length=50,
        blank=True,
        default="PENDING",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    deduplication_key = models.CharField(
        max_length=150,
        unique=True,
        editable=False,
    )

    class Meta:
        ordering = ["-created_at"]

        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(
                        rent_record__isnull=False,
                        electricity_bill__isnull=True,
                    )
                    | Q(
                        rent_record__isnull=True,
                        electricity_bill__isnull=False,
                    )
                ),
                name="notification_has_exactly_one_bill",
            ),
        ]

    def clean(self):
        super().clean()

        if bool(self.rent_record_id) == bool(
            self.electricity_bill_id
        ):
            raise ValidationError(
                "Notification must be linked to exactly one bill."
            )

        if self.rent_record_id:
            if (
                self.tenant_id
                and self.rent_record.agreement.tenant_id
                != self.tenant_id
            ):
                raise ValidationError({
                    "tenant": (
                        "Tenant must match the rent record agreement."
                    )
                })

        if self.electricity_bill_id:
            if self.tenant_id:
                room_id = self.electricity_bill.meter.room_id

                has_active_agreement = (
                    self.tenant.agreements.filter(
                        room_id=room_id,
                        status="ACTIVE",
                    ).exists()
                )

                if not has_active_agreement:
                    raise ValidationError({
                        "tenant": (
                            "Tenant must have an active agreement "
                            "for the electricity bill's room."
                        )
                    })

    def save(self, *args, **kwargs):
        if bool(self.rent_record_id) == bool(
            self.electricity_bill_id
        ):
            raise ValidationError(
                "Notification must be linked to exactly one bill."
            )

        if self.notification_type not in dict(
            self.NOTIFICATION_TYPES
        ):
            raise ValidationError(
                "Invalid notification type."
            )

        if self.rent_record_id:
            bill_key = f"rent:{self.rent_record_id}"
        else:
            bill_key = f"electricity:{self.electricity_bill_id}"

        self.deduplication_key = (
            f"{self.tenant_id}:{bill_key}:"
            f"{self.notification_type}"
        )

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tenant.full_name} - {self.title}"
