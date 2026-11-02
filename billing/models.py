
from django.conf import settings
from django.db import models


class RentRecord(models.Model):
    PAYMENT_STATUSES = [
        ("PENDING", "Pending"),
        ("PARTIAL", "Partially Paid"),
        ("PAID", "Paid"),
        ("OVERDUE", "Overdue"),
    ]

    agreement = models.ForeignKey(
        "tenants.RentalAgreement",
        on_delete=models.PROTECT,
        related_name="rent_records",
    )

    billing_month = models.DateField()
    rent_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    due_date = models.DateField()

    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUSES,
        default="PENDING",
    )

    notes = models.TextField(blank=True)
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["agreement", "billing_month"],
                name="unique_rent_record_per_month",
            )
        ]
        ordering = ["-billing_month", "agreement_id"]

    def __str__(self):
        return (
            f"{self.agreement} - "
            f"{self.billing_month:%B %Y}"
        )


class BillingArchive(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="billing_archives",
    )
    property = models.ForeignKey(
        "properties.Property",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="billing_archives",
    )
    billing_month = models.DateField()
    total_tenants = models.PositiveIntegerField(default=0)
    total_billed = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    total_paid = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    total_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    archived_at = models.DateTimeField(auto_now_add=True)
    snapshot_data = models.JSONField(default=list, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-billing_month", "-archived_at"]

    def __str__(self):
        prop_str = (
            f" - {self.property.name}"
            if self.property
            else ""
        )
        return (
            f"Archive {self.billing_month:%B %Y}"
            f"{prop_str}"
        )


class OwnerQrConfig(models.Model):
    """UPI QR profiles created by a property owner."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owner_qr_configs",
    )
    label = models.CharField(max_length=120)
    payee_name = models.CharField(max_length=160)
    upi_id = models.CharField(max_length=160)

    # Exact owner-uploaded QR image.
    # No default or automatically generated QR is used.
    qr_image_data_url = models.TextField()

    property_name = models.CharField(
        max_length=160,
        blank=True,
        default="",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["label", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "label"],
                name="unique_owner_qr_profile_label",
            )
        ]

    def __str__(self):
        return f"{self.label} ({self.upi_id})"


class TenantQrAssignment(models.Model):
    """The QR profile assigned to a tenant by their property owner."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tenant_qr_assignments",
    )

    # Tenant database ID. Ownership is verified by the API.
    tenant_id = models.PositiveBigIntegerField()

    qr_config = models.ForeignKey(
        OwnerQrConfig,
        on_delete=models.CASCADE,
        related_name="tenant_assignments",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["tenant_id"]
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "tenant_id"],
                name="unique_owner_tenant_qr_assignment",
            )
        ]

    def __str__(self):
        return (
            f"Tenant {self.tenant_id} "
            f"-> QR {self.qr_config_id}"
        )
