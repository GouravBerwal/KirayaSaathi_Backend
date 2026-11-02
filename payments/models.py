
from django.db import models
from django.core.exceptions import ValidationError


class Payment(models.Model):

    PAYMENT_METHODS = [
        ("CASH", "Cash"),
        ("UPI", "UPI"),
        ("BANK_TRANSFER", "Bank Transfer"),
        ("CARD", "Card"),
        ("OTHER", "Other"),
    ]

    PAYMENT_STATUSES = [
        ("PENDING", "Pending"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
        ("REFUNDED", "Refunded"),
    ]

    # Rental agreement linked to this payment
    agreement = models.ForeignKey(
        "tenants.RentalAgreement",
        on_delete=models.PROTECT,
        related_name="payments"
    )

    # Link payment to a rent record OR an electricity bill
    rent_record = models.ForeignKey(
        "billing.RentRecord",
        on_delete=models.PROTECT,
        related_name="payments",
        null=True,
        blank=True
    )

    electricity_bill = models.ForeignKey(
        "electricity.ElectricityBill",
        on_delete=models.PROTECT,
        related_name="payments",
        null=True,
        blank=True
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    payment_date = models.DateTimeField()

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS
    )

    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUSES,
        default="COMPLETED"
    )

    transaction_reference = models.CharField(
        max_length=100,
        blank=True
    )

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(
                        rent_record__isnull=False,
                        electricity_bill__isnull=True
                    )
                    | models.Q(
                        rent_record__isnull=True,
                        electricity_bill__isnull=False
                    )
                ),
                name="payment_has_exactly_one_bill"
            )
        ]

    def clean(self):
        super().clean()

        if bool(self.rent_record_id) == bool(self.electricity_bill_id):
            raise ValidationError(
                "Payment must be linked to exactly one rent "
                "or electricity bill."
            )

        if (
            self.rent_record_id
            and self.agreement_id
            and self.rent_record.agreement_id != self.agreement_id
        ):
            raise ValidationError(
                "Rent record must belong to the same rental agreement."
            )

        if (
            self.electricity_bill_id
            and self.agreement_id
            and self.electricity_bill.meter.room_id
            != self.agreement.room_id
        ):
            raise ValidationError(
                "Electricity bill must belong to the agreement's room."
            )

        if self.agreement_id and self.agreement.tenant.owner_id != self.agreement.room.property.owner_id:
            raise ValidationError(
                "Agreement tenant and room must belong to the same owner."
            )

    def __str__(self):
        return f"{self.agreement} - Rs. {self.amount}"
