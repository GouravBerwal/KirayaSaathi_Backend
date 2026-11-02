from decimal import Decimal

from django.db.models import Sum, Q
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response

from properties.models import Room
from tenants.models import RentalAgreement
from billing.models import RentRecord, BillingArchive
from electricity.models import ElectricityBill
from payments.models import Payment


def money(value):
    amount = Decimal(str(value if value is not None else "0.00"))
    return str(amount.quantize(Decimal("0.01")))


def next_month_date(d):
    """Return the first day of the next month."""
    if d.month == 12:
        return d.replace(year=d.year + 1, month=1, day=1)
    return d.replace(month=d.month + 1, day=1)


def calculate_bill_summary(records, amount_field):
    total_amount = Decimal("0.00")
    total_paid = Decimal("0.00")
    outstanding = Decimal("0.00")
    overdue_amount = Decimal("0.00")
    pending_count = 0
    overdue_count = 0
    today = timezone.localdate()

    for amount, paid, due_date in records.values_list(
        amount_field, "amount_paid", "due_date"
    ):
        amount = amount or Decimal("0.00")
        paid = paid or Decimal("0.00")
        remaining = max(Decimal("0.00"), amount - paid)

        total_amount += amount
        total_paid += paid
        outstanding += remaining

        if remaining > 0:
            pending_count += 1

            if due_date and due_date < today:
                overdue_amount += remaining
                overdue_count += 1

    return {
        "total_billed": money(total_amount),
        "total_paid_towards_bills": money(total_paid),
        "pending_amount": money(outstanding),
        "overdue_amount": money(overdue_amount),
        "pending_records": pending_count,
        "overdue_records": overdue_count,
    }


class DashboardSummaryAPIView(APIView):

    def get(self, request):
        owner = request.user
        today = timezone.localdate()
        month_start = today.replace(day=1)

        # Owner ke rooms
        rooms = Room.objects.filter(property__owner=owner)

        # Owner ke rental agreements
        agreements = RentalAgreement.objects.filter(
            room__property__owner=owner,
            tenant__owner=owner,
        )

        # Owner ke rent records (both active and archived)
        rent_records = RentRecord.objects.filter(
            agreement__room__property__owner=owner,
            agreement__tenant__owner=owner,
        )

        # Owner ke electricity bills
        electricity_bills = ElectricityBill.objects.filter(
            meter__room__property__owner=owner
        )

        # Owner ke payments
        payments = Payment.objects.filter(
            agreement__room__property__owner=owner
        )

        # Owner ke billing archives
        billing_archives = BillingArchive.objects.filter(owner=owner)

        # Room summary
        total_rooms = rooms.count()
        occupied_rooms = rooms.filter(status="OCCUPIED").count()
        vacant_rooms = rooms.filter(status="VACANT").count()
        maintenance_rooms = rooms.filter(status="MAINTENANCE").count()

        # Active tenants and agreements
        active_agreements = agreements.filter(status="ACTIVE")
        active_tenants = (
            active_agreements.values("tenant_id").distinct().count()
        )

        # Determine current active billing cycle:
        # If any unarchived rent records exist, use their billing month.
        # If archive rolled over into next month or records exist for next month, use that!
        latest_unarchived_rec = (
            rent_records.filter(is_archived=False)
            .order_by("-billing_month")
            .first()
        )
        latest_rec = rent_records.order_by("-billing_month").first()
        latest_archive = billing_archives.order_by("-billing_month").first()

        active_month_start = month_start
        if latest_unarchived_rec and latest_unarchived_rec.billing_month:
            active_month_start = latest_unarchived_rec.billing_month.replace(day=1)
        elif latest_rec and latest_rec.billing_month and latest_rec.billing_month > month_start:
            active_month_start = latest_rec.billing_month.replace(day=1)
        elif latest_archive and latest_archive.billing_month:
            arch_next = next_month_date(latest_archive.billing_month)
            if arch_next > active_month_start:
                active_month_start = arch_next

        # Current active cycle rent records
        current_month_rent = rent_records.filter(
            billing_month__year=active_month_start.year,
            billing_month__month=active_month_start.month,
            is_archived=False,
        )
        if not current_month_rent.exists():
            current_month_rent = rent_records.filter(
                billing_month__year=active_month_start.year,
                billing_month__month=active_month_start.month,
            )

        rent_summary = calculate_bill_summary(
            current_month_rent,
            "rent_amount",
        )

        # Current active cycle electricity bills
        current_month_electricity = electricity_bills.filter(
            billing_month__year=active_month_start.year,
            billing_month__month=active_month_start.month,
        )

        electricity_summary = calculate_bill_summary(
            current_month_electricity,
            "total_amount",
        )

        # Completed payments only
        completed_payments = payments.filter(status="COMPLETED")

        # Rent collected during the active billing cycle
        current_month_rent_payments = completed_payments.filter(
            rent_record__isnull=False,
        ).filter(
            Q(payment_date__year=active_month_start.year, payment_date__month=active_month_start.month)
            | Q(rent_record__billing_month__year=active_month_start.year, rent_record__billing_month__month=active_month_start.month)
        )

        rent_collected_from_payments = (
            current_month_rent_payments.aggregate(
                total=Sum("amount")
            )["total"]
            or Decimal("0.00")
        )

        rent_collected_from_records = (
            current_month_rent.aggregate(
                total=Sum("amount_paid")
            )["total"]
            or Decimal("0.00")
        )

        rent_collected = max(rent_collected_from_payments, rent_collected_from_records)

        # Electricity payments collected during the active billing cycle
        current_month_electricity_payments = completed_payments.filter(
            electricity_bill__isnull=False,
        ).filter(
            Q(payment_date__year=active_month_start.year, payment_date__month=active_month_start.month)
            | Q(electricity_bill__billing_month__year=active_month_start.year, electricity_bill__billing_month__month=active_month_start.month)
        )

        electricity_collected_from_payments = (
            current_month_electricity_payments.aggregate(
                total=Sum("amount")
            )["total"]
            or Decimal("0.00")
        )

        electricity_collected_from_records = (
            current_month_electricity.aggregate(
                total=Sum("amount_paid")
            )["total"]
            or Decimal("0.00")
        )

        electricity_collected = max(electricity_collected_from_payments, electricity_collected_from_records)

        # Total completed payments across rent and electricity
        total_collected = (
            completed_payments.aggregate(
                total=Sum("amount")
            )["total"]
            or Decimal("0.00")
        )

        # Rental Income Chart:
        # Determine latest month to display (e.g. forward-looking to newly rolled-over month after archive)
        end_chart_month = active_month_start
        if latest_rec and latest_rec.billing_month:
            rec_m = latest_rec.billing_month.replace(day=1)
            if rec_m > end_chart_month:
                end_chart_month = rec_m
        if latest_archive and latest_archive.billing_month:
            arch_next = next_month_date(latest_archive.billing_month)
            if arch_next > end_chart_month:
                end_chart_month = arch_next

        # Step back 5 months from end_chart_month to get the start of the 6-month window
        month_cursor = end_chart_month
        for _ in range(5):
            month_cursor = (
                month_cursor.replace(day=1)
                - timezone.timedelta(days=1)
            ).replace(day=1)

        income_chart_months = []
        for _ in range(6):
            year = month_cursor.year
            month = month_cursor.month

            expected_amount = (
                rent_records.filter(
                    billing_month__year=year,
                    billing_month__month=month,
                ).aggregate(total=Sum("rent_amount"))["total"]
                or Decimal("0.00")
            )

            paid_from_records = (
                rent_records.filter(
                    billing_month__year=year,
                    billing_month__month=month,
                ).aggregate(total=Sum("amount_paid"))["total"]
                or Decimal("0.00")
            )

            paid_from_payments_linked = (
                completed_payments.filter(
                    rent_record__billing_month__year=year,
                    rent_record__billing_month__month=month,
                ).aggregate(total=Sum("amount"))["total"]
                or Decimal("0.00")
            )

            paid_from_payment_date = (
                completed_payments.filter(
                    rent_record__isnull=False,
                    payment_date__year=year,
                    payment_date__month=month,
                ).aggregate(total=Sum("amount"))["total"]
                or Decimal("0.00")
            )

            collected_amount = max(
                paid_from_records,
                paid_from_payments_linked,
                paid_from_payment_date,
            )

            # Historical archive snapshot fallback
            arch = billing_archives.filter(
                billing_month__year=year,
                billing_month__month=month,
            ).first()
            if arch:
                if expected_amount == Decimal("0.00") and arch.total_billed:
                    expected_amount = arch.total_billed
                if collected_amount == Decimal("0.00") and arch.total_paid:
                    collected_amount = arch.total_paid

            income_chart_months.append({
                "month": month_cursor.strftime("%b"),
                "year": year,
                "expected": money(expected_amount),
                "collected": money(collected_amount),
            })

            # Next month
            month_cursor = next_month_date(month_cursor)

        # Recent payments
        recent_payments = (
            payments.select_related(
                "agreement__tenant",
                "rent_record",
                "electricity_bill",
            )
            .order_by("-payment_date", "-pk")[:5]
        )

        recent_payment_data = []

        for payment in recent_payments:
            if payment.rent_record_id:
                bill_type = "RENT"
                bill_id = payment.rent_record_id
            elif payment.electricity_bill_id:
                bill_type = "ELECTRICITY"
                bill_id = payment.electricity_bill_id
            else:
                bill_type = None
                bill_id = None

            tenant_name = "Tenant"
            if payment.agreement and getattr(payment.agreement, "tenant", None):
                tenant_name = payment.agreement.tenant.full_name or "Tenant"

            recent_payment_data.append({
                "id": payment.pk,
                "tenant": tenant_name,
                "amount": money(payment.amount),
                "payment_date": payment.payment_date.isoformat(),
                "payment_method": payment.payment_method,
                "status": payment.status,
                "bill_type": bill_type,
                "bill_id": bill_id,
                "transaction_reference": payment.transaction_reference,
            })

        return Response({
            "generated_at": timezone.now().isoformat(),

            "income_chart": {
                "months": income_chart_months,
            },

            "rooms": {
                "total": total_rooms,
                "occupied": occupied_rooms,
                "vacant": vacant_rooms,
                "maintenance": maintenance_rooms,
            },

            "tenants": {
                "active": active_tenants,
                "active_agreements": active_agreements.count(),
            },

            "rent": {
                **rent_summary,
                "current_month_collected": money(rent_collected),
                "current_month_pending": money(
                    min(
                        Decimal(rent_summary["pending_amount"]),
                        max(Decimal("0.00"), Decimal(rent_summary["total_billed"]) - rent_collected),
                    )
                ),
                "current_month_billed": rent_summary["total_billed"],
            },

            "electricity": {
                **electricity_summary,
                "current_month_collected": money(electricity_collected),
                "current_month_pending": money(
                    min(
                        Decimal(electricity_summary["pending_amount"]),
                        max(Decimal("0.00"), Decimal(electricity_summary["total_billed"]) - electricity_collected),
                    )
                ),
                "current_month_billed": electricity_summary["total_billed"],
            },

            "payments": {
                "completed_payment_count": completed_payments.count(),
                "total_collected": money(total_collected),
                "recent": recent_payment_data,
            },
        })
