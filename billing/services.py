import calendar
from datetime import date
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from tenants.models import RentalAgreement
from properties.models import Property
from electricity.models import ElectricityMeter, MeterReading, ElectricityBill
from .models import RentRecord, BillingArchive


def month_start(value):
    """Return the first day of the given month."""
    if isinstance(value, str):
        parts = value.strip().split("-")
        return date(int(parts[0]), int(parts[1]), 1)
    return date(value.year, value.month, 1)


def next_month(value):
    """Return the first day of the next month."""
    if value.month == 12:
        return date(value.year + 1, 1, 1)
    return date(value.year, value.month + 1, 1)


def calculate_due_date(billing_month, due_day):
    """Keep the due day within the month's valid date range."""
    last_day = calendar.monthrange(
        billing_month.year,
        billing_month.month,
    )[1]

    safe_day = max(1, min(due_day, last_day))

    return date(
        billing_month.year,
        billing_month.month,
        safe_day,
    )


@transaction.atomic
def generate_monthly_rent_records(as_of=None, owner=None):
    """
    Generate missing rent records for ACTIVE agreements,
    from the agreement's start month through the as-of month.

    Existing records are never overwritten.
    When owner is provided, only that owner's agreements are processed.
    """
    if as_of is None:
        as_of = timezone.localdate()

    current_month = month_start(as_of)

    agreements = (
        RentalAgreement.objects
        .filter(status="ACTIVE")
        .select_related("tenant", "room", "room__property")
        .order_by("pk")
    )
    if owner is not None:
        agreements = agreements.filter(room__property__owner=owner)

    created_count = 0
    existing_count = 0

    for agreement in agreements:
        start_month = month_start(agreement.start_date)

        # Agreement has not started yet.
        if start_month > current_month:
            continue

        final_month = current_month

        # Do not generate records beyond the agreement's end month.
        if agreement.end_date:
            end_month = month_start(agreement.end_date)
            final_month = min(final_month, end_month)

        if start_month > final_month:
            continue

        billing_month_val = start_month
        due_day = agreement.room.property.rent_due_day

        while billing_month_val <= final_month:
            due_date = calculate_due_date(
                billing_month_val,
                due_day,
            )

            initial_status = (
                "OVERDUE"
                if due_date < as_of
                else "PENDING"
            )

            _, created = RentRecord.objects.get_or_create(
                agreement=agreement,
                billing_month=billing_month_val,
                defaults={
                    "rent_amount": agreement.monthly_rent,
                    "due_date": due_date,
                    "amount_paid": 0,
                    "status": initial_status,
                },
            )

            if created:
                created_count += 1
            else:
                existing_count += 1

            billing_month_val = next_month(billing_month_val)

    return {
        "created": created_count,
        "already_existing": existing_count,
    }


@transaction.atomic
def archive_billing_month(owner, billing_month, property_id=None, notes=""):
    """
    Archive a completed month's billing data for an owner:
    1. Mark all RentRecords for that month as is_archived=True.
    2. Collect all tenant rent & electricity bills into a permanent JSON snapshot.
    3. Save BillingArchive record.
    4. Automatically rollover electricity meter readings for the next month:
       - The archived month's current_reading becomes next month's previous_reading.
       - Ensures subsequent electricity calculations continue smoothly.
    """
    target_month = month_start(billing_month)
    next_month_date = next_month(target_month)
    now = timezone.now()

    prop_obj = None
    if property_id:
        prop_obj = Property.objects.filter(pk=property_id, owner=owner).first()

    # 1. Query RentRecords
    records_qs = RentRecord.objects.filter(
        agreement__room__property__owner=owner,
        billing_month=target_month,
    ).select_related(
        "agreement__tenant",
        "agreement__room",
        "agreement__room__property",
    )

    if prop_obj:
        records_qs = records_qs.filter(agreement__room__property=prop_obj)

    # Mark active rent records as archived
    records_qs.update(is_archived=True, archived_at=now)

    # 2. Query ElectricityBills for the same month
    elec_bills_qs = ElectricityBill.objects.filter(
        meter__room__property__owner=owner,
        billing_month=target_month,
    ).select_related("meter", "reading", "meter__room")

    if prop_obj:
        elec_bills_qs = elec_bills_qs.filter(meter__room__property=prop_obj)

    elec_bill_by_room = {b.meter.room_id: b for b in elec_bills_qs}

    # 3. Build snapshot list
    snapshot_items = []
    total_billed = Decimal("0.00")
    total_paid = Decimal("0.00")
    total_balance = Decimal("0.00")
    tenant_ids_seen = set()

    for r in records_qs:
        tenant = r.agreement.tenant
        room = r.agreement.room
        prop = room.property
        tenant_ids_seen.add(tenant.pk)

        elec_bill = elec_bill_by_room.get(room.pk)
        elec_amount = elec_bill.total_amount if elec_bill else Decimal("0.00")
        elec_paid = elec_bill.amount_paid if elec_bill else Decimal("0.00")
        elec_units = elec_bill.units_consumed if elec_bill else Decimal("0.00")
        elec_rate = elec_bill.rate_per_unit if elec_bill else (prop.electricity_rate or Decimal("8.00"))
        prev_reading = elec_bill.reading.previous_reading if (elec_bill and elec_bill.reading) else Decimal("0.00")
        curr_reading = elec_bill.reading.current_reading if (elec_bill and elec_bill.reading) else Decimal("0.00")

        rent_due = r.rent_amount
        rent_paid = r.amount_paid
        item_total_billed = rent_due + elec_amount
        item_total_paid = rent_paid + elec_paid
        item_balance = max(Decimal("0.00"), item_total_billed - item_total_paid)

        total_billed += item_total_billed
        total_paid += item_total_paid
        total_balance += item_balance

        snapshot_items.append({
            "record_id": r.pk,
            "tenant_id": tenant.pk,
            "tenant_name": tenant.full_name,
            "tenant_phone": tenant.phone,
            "property_id": prop.pk,
            "property_name": prop.name,
            "room_id": room.pk,
            "room_number": room.room_number,
            "billing_month": target_month.isoformat(),
            "due_date": r.due_date.isoformat(),
            "rent_amount": str(rent_due),
            "rent_paid": str(rent_paid),
            "rent_balance": str(max(Decimal("0.00"), rent_due - rent_paid)),
            "rent_status": r.status,
            "meter_number": elec_bill.meter.meter_number if elec_bill else f"MTR-{room.room_number}",
            "previous_reading": str(prev_reading),
            "current_reading": str(curr_reading),
            "units_consumed": str(elec_units),
            "rate_per_unit": str(elec_rate),
            "electricity_amount": str(elec_amount),
            "electricity_paid": str(elec_paid),
            "electricity_status": elec_bill.status if elec_bill else "N/A",
            "total_billed": str(item_total_billed),
            "total_paid": str(item_total_paid),
            "balance": str(item_balance),
        })

    # Save BillingArchive record
    archive, _ = BillingArchive.objects.update_or_create(
        owner=owner,
        billing_month=target_month,
        property=prop_obj,
        defaults={
            "total_tenants": len(tenant_ids_seen),
            "total_billed": total_billed,
            "total_paid": total_paid,
            "total_balance": total_balance,
            "snapshot_data": snapshot_items,
            "notes": notes,
        },
    )

    # 4. ELECTRICITY READING ROLLOVER FOR NEXT MONTH
    # For every active meter, take the archived month's current_reading
    # and set it as next month's previous_reading.
    meters_qs = ElectricityMeter.objects.filter(
        room__property__owner=owner,
        is_active=True,
    ).select_related("room", "room__property")

    if prop_obj:
        meters_qs = meters_qs.filter(room__property=prop_obj)

    last_day_of_target_month = calendar.monthrange(target_month.year, target_month.month)[1]
    target_month_end = date(target_month.year, target_month.month, last_day_of_target_month)

    rollover_count = 0
    for meter in meters_qs:
        # Find latest reading for this meter on or before target month end
        latest_reading = (
            MeterReading.objects
            .filter(meter=meter, reading_date__lte=target_month_end)
            .order_by("-reading_date")
            .first()
        )
        if not latest_reading:
            latest_reading = MeterReading.objects.filter(meter=meter).order_by("-reading_date").first()

        if latest_reading:
            archived_curr = latest_reading.current_reading

            # Find or initialize reading for next month
            next_reading = MeterReading.objects.filter(
                meter=meter,
                reading_date=next_month_date,
            ).first()

            if next_reading:
                next_reading.previous_reading = archived_curr
                if next_reading.current_reading < archived_curr:
                    next_reading.current_reading = archived_curr
                next_reading.save(update_fields=["previous_reading", "current_reading"])
            else:
                MeterReading.objects.create(
                    meter=meter,
                    reading_date=next_month_date,
                    previous_reading=archived_curr,
                    current_reading=archived_curr,
                    notes=f"Auto-rollover from {target_month.strftime('%B %Y')} reading ({archived_curr})"
                )
            rollover_count += 1

    # 5. Automatically generate new month's fresh rent records for all active agreements!
    # These will have status='PENDING' and amount_paid=0.00 so the new month starts fresh with 0 collected.
    generate_monthly_rent_records(as_of=next_month_date, owner=owner)

    return {
        "archive": archive,
        "records_archived": records_qs.count(),
        "meters_rolled_over": rollover_count,
        "next_month": next_month_date.isoformat(),
    }
