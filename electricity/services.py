
from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError

from .models import ElectricityMeter, MeterReading


def calculate_units_consumed(previous_reading, current_reading):
    previous_reading = Decimal(str(previous_reading))
    current_reading = Decimal(str(current_reading))

    if current_reading < previous_reading:
        raise ValidationError(
            "Current reading previous reading se kam nahi ho sakti."
        )

    return current_reading - previous_reading


def calculate_electricity_amount(units_consumed, rate_per_unit):
    units_consumed = Decimal(str(units_consumed))
    rate_per_unit = Decimal(str(rate_per_unit))

    if units_consumed < 0:
        raise ValidationError("Units negative nahi ho sakte.")

    if rate_per_unit < 0:
        raise ValidationError("Electricity rate negative nahi ho sakta.")

    total = units_consumed * rate_per_unit

    return total.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )


import calendar
from datetime import date

from django.db import transaction
from django.utils import timezone

from .models import ElectricityBill


def calculate_electricity_due_date(billing_month, due_day):
    last_day = calendar.monthrange(
        billing_month.year,
        billing_month.month
    )[1]

    safe_day = min(max(due_day, 1), last_day)

    return date(
        billing_month.year,
        billing_month.month,
        safe_day
    )


@transaction.atomic
def generate_electricity_bill(reading_id, billing_month=None, owner=None):
    reading = (
        MeterReading.objects
        .select_for_update()
        .select_related("meter", "meter__room__property")
        .get(pk=reading_id)
    )

    meter = reading.meter
    if owner is not None and meter.room.property.owner_id != owner.pk:
        # Use a not-found response at the API boundary so another owner's
        # reading IDs cannot be confirmed by probing this endpoint.
        raise MeterReading.DoesNotExist

    if not meter.is_active:
        raise ValidationError(
            "Inactive meter ka bill generate nahi kar sakte."
        )

    if billing_month is None:
        billing_month = reading.reading_date.replace(day=1)
    else:
        billing_month = billing_month.replace(day=1)

    existing_bill = ElectricityBill.objects.filter(
        reading=reading
    ).first()

    if existing_bill:
        return existing_bill, False

    units = calculate_units_consumed(
        reading.previous_reading,
        reading.current_reading
    )

    rate = meter.room.property.electricity_rate

    total_amount = calculate_electricity_amount(
        units,
        rate
    )

    due_date = calculate_electricity_due_date(
        billing_month,
        meter.room.property.rent_due_day
    )

    bill = ElectricityBill.objects.create(
        meter=meter,
        reading=reading,
        billing_month=billing_month,
        units_consumed=units,
        rate_per_unit=rate,
        total_amount=total_amount,
        due_date=due_date,
        amount_paid=0,
        status=(
            "OVERDUE"
            if due_date < timezone.localdate()
            else "PENDING"
        )
    )

    return bill, True
