from django.db import models

# Create your models here.

class ElectricityMeter(models.Model):
    room = models.ForeignKey(
        "properties.Room",
        on_delete=models.PROTECT,
        related_name="electricity_meters"
    )
    meter_number = models.CharField(max_length=50, unique=True)
    installation_date = models.DateField()
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Meter {self.meter_number} - Room {self.room.room_number}"


class MeterReading(models.Model):
    meter = models.ForeignKey(
        ElectricityMeter,
        on_delete=models.PROTECT,
        related_name="readings"
    )
    reading_date = models.DateField()
    previous_reading = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )
    current_reading = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-reading_date"]
        constraints = [
            models.UniqueConstraint(
                fields=["meter", "reading_date"],
                name="unique_meter_reading_per_date"
            )
        ]

    def __str__(self):
        return f"{self.meter.meter_number} - {self.reading_date}"


class ElectricityBill(models.Model):
    PAYMENT_STATUSES = [
        ("PENDING", "Pending"),
        ("PARTIAL", "Partially Paid"),
        ("PAID", "Paid"),
        ("OVERDUE", "Overdue"),
    ]

    meter = models.ForeignKey(
        ElectricityMeter,
        on_delete=models.PROTECT,
        related_name="bills"
    )
    reading = models.ForeignKey(
        MeterReading,
        on_delete=models.PROTECT,
        related_name="bills"
    )
    billing_month = models.DateField()
    units_consumed = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    rate_per_unit = models.DecimalField(
        max_digits=8,
        decimal_places=2
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    due_date = models.DateField()
    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUSES,
        default="PENDING"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["reading"],
                name="unique_electricity_bill_per_reading",
            )
        ]

    def __str__(self):
        return f"{self.meter.meter_number} - {self.billing_month:%B %Y}"
