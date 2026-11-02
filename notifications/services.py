
from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from billing.models import RentRecord
from electricity.models import ElectricityBill
from tenants.models import RentalAgreement
from .models import Notification


def get_outstanding_amount(total_amount, amount_paid):
    remaining = (
        Decimal(str(total_amount))
        - Decimal(str(amount_paid or 0))
    )
    return max(Decimal("0.00"), remaining)


@transaction.atomic
def generate_notifications(days_ahead=3, as_of=None, owner=None):
    if not isinstance(days_ahead, int) or isinstance(days_ahead, bool):
        raise ValueError("days_ahead ek integer hona chahiye.")

    if days_ahead < 0 or days_ahead > 365:
        raise ValueError("days_ahead 0 se 365 ke beech hona chahiye.")

    if as_of is None:
        as_of = timezone.localdate()

    last_reminder_date = as_of + timedelta(days=days_ahead)

    created_count = 0

    # Rent reminders
    rent_records = RentRecord.objects.select_related(
        "agreement__tenant", "agreement__room__property"
    ).all()
    if owner is not None:
        rent_records = rent_records.filter(
            agreement__room__property__owner=owner,
            agreement__tenant__owner=owner,
        )

    for record in rent_records:
        outstanding = get_outstanding_amount(
            record.rent_amount,
            record.amount_paid,
        )

        if outstanding <= 0:
            continue

        if record.due_date < as_of:
            notification_type = "RENT_OVERDUE"
            title = "Rent Payment Overdue"
            message = (
                f"{record.agreement.tenant.full_name}, "
                f"aapka rent overdue hai. "
                f"Pending amount: Rs. {outstanding}. "
                f"Due date: {record.due_date}."
            )
        elif record.due_date <= last_reminder_date:
            notification_type = "RENT_UPCOMING"
            title = "Rent Payment Due Soon"
            message = (
                f"{record.agreement.tenant.full_name}, "
                f"aapka rent {record.due_date} ko due hai. "
                f"Pending amount: Rs. {outstanding}."
            )
        else:
            continue

        _, created = Notification.objects.get_or_create(
            tenant=record.agreement.tenant,
            rent_record=record,
            electricity_bill=None,
            notification_type=notification_type,
            defaults={
                "title": title,
                "message": message,
                "due_date": record.due_date,
                "amount_due": outstanding,
            },
        )

        if created:
            created_count += 1

    # Electricity bill reminders
    electricity_bills = ElectricityBill.objects.select_related(
        "meter", "meter__room", "meter__room__property"
    ).all()
    if owner is not None:
        electricity_bills = electricity_bills.filter(
            meter__room__property__owner=owner
        )

    for bill in electricity_bills:
        outstanding = get_outstanding_amount(
            bill.total_amount,
            bill.amount_paid,
        )

        if outstanding <= 0:
            continue

        # Electricity bill ko us room ke active tenant se link karo.
        agreements = RentalAgreement.objects.select_related("tenant").filter(
            room_id=bill.meter.room_id,
            status="ACTIVE",
            room__property__owner=(
                owner if owner is not None else bill.meter.room.property.owner
            ),
        )
        if owner is not None:
            agreements = agreements.filter(tenant__owner=owner)
        agreement = agreements.order_by("-start_date", "-pk").first()

        # Active tenant nahi hai toh tenant-specific reminder skip karo.
        if agreement is None:
            continue

        if bill.due_date < as_of:
            notification_type = "ELECTRICITY_OVERDUE"
            title = "Electricity Bill Overdue"
            message = (
                f"{agreement.tenant.full_name}, "
                f"aapka electricity bill overdue hai. "
                f"Pending amount: Rs. {outstanding}. "
                f"Due date: {bill.due_date}."
            )
        elif bill.due_date <= last_reminder_date:
            notification_type = "ELECTRICITY_UPCOMING"
            title = "Electricity Bill Due Soon"
            message = (
                f"{agreement.tenant.full_name}, "
                f"aapka electricity bill {bill.due_date} ko due hai. "
                f"Pending amount: Rs. {outstanding}."
            )
        else:
            continue

        _, created = Notification.objects.get_or_create(
            tenant=agreement.tenant,
            rent_record=None,
            electricity_bill=bill,
            notification_type=notification_type,
            defaults={
                "title": title,
                "message": message,
                "due_date": bill.due_date,
                "amount_due": outstanding,
            },
        )

        if created:
            created_count += 1

    return {
        "created_count": created_count,
        "as_of": as_of,
        "days_ahead": days_ahead,
    }
