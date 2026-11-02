
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from billing.models import RentRecord
from electricity.models import ElectricityBill
from .models import Payment


def calculate_bill_status(total_amount, amount_paid, due_date):
    if total_amount > 0 and amount_paid >= total_amount:
        return "PAID"

    if amount_paid > 0:
        return "PARTIAL"

    if due_date < timezone.localdate():
        return "OVERDUE"

    return "PENDING"


def sync_rent_records(record_ids):
    for record in RentRecord.objects.select_for_update().filter(
        pk__in=record_ids
    ).order_by("pk"):
        total_paid = Payment.objects.filter(
            rent_record=record,
            status="COMPLETED",
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

        record.amount_paid = total_paid
        record.status = calculate_bill_status(
            record.rent_amount,
            total_paid,
            record.due_date,
        )
        record.save(update_fields=["amount_paid", "status", "updated_at"])


def sync_electricity_bills(bill_ids):
    for bill in ElectricityBill.objects.select_for_update().filter(
        pk__in=bill_ids
    ).order_by("pk"):
        total_paid = Payment.objects.filter(
            electricity_bill=bill,
            status="COMPLETED",
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

        bill.amount_paid = total_paid
        bill.status = calculate_bill_status(
            bill.total_amount,
            total_paid,
            bill.due_date,
        )
        bill.save(update_fields=["amount_paid", "status", "updated_at"])


def sync_payment_bills(rent_record_ids=None, electricity_bill_ids=None):
    sync_rent_records(set(rent_record_ids or []))
    sync_electricity_bills(set(electricity_bill_ids or []))
