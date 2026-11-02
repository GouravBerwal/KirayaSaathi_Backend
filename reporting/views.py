
from datetime import date
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from accounts.permissions import IsVerifiedOwner
from rest_framework.response import Response
from rest_framework.views import APIView

from properties.models import Property, Room
from tenants.models import RentalAgreement
from billing.models import RentRecord
from electricity.models import ElectricityBill
from payments.models import Payment


def money(value):
    value = value or Decimal("0.00")
    return str(Decimal(str(value)).quantize(Decimal("0.01")))


def month_range(start_date, end_date):
    current = start_date.replace(day=1)
    months = []

    while current <= end_date:
        months.append(current)

        if current.month == 12:
            current = current.replace(
                year=current.year + 1,
                month=1,
            )
        else:
            current = current.replace(
                month=current.month + 1,
            )

    return months


class ReportsAPIView(APIView):
    permission_classes = [IsVerifiedOwner]

    def get(self, request):
        owner = request.user
        today = timezone.localdate()

        # Optional filters: YYYY-MM-DD
        start_value = request.query_params.get("start_date")
        end_value = request.query_params.get("end_date")
        property_value = request.query_params.get("property_id")

        try:
            end_date = date.fromisoformat(end_value) if end_value else today
            default_start = end_date.replace(day=1)
            start_date = (
                date.fromisoformat(start_value)
                if start_value
                else default_start
            )
        except ValueError:
            return Response(
                {
                    "error": (
                        "Invalid date. Use YYYY-MM-DD "
                        "for start_date and end_date."
                    )
                },
                status=400,
            )

        if start_date > end_date:
            return Response(
                {"error": "start_date must be before end_date."},
                status=400,
            )

        properties = Property.objects.filter(owner=owner)

        if property_value and property_value != "all":
            try:
                property_id = int(property_value)
            except ValueError:
                return Response(
                    {"error": "property_id must be a valid property ID."},
                    status=400,
                )

            properties = properties.filter(pk=property_id)

            if not properties.exists():
                return Response(
                    {"error": "Property not found."},
                    status=404,
                )

        property_ids = list(
            properties.values_list("id", flat=True)
        )

        rooms = Room.objects.filter(property_id__in=property_ids)

        agreements = RentalAgreement.objects.filter(
            room__property_id__in=property_ids,
            tenant__owner=owner,
        )

        rent_records = RentRecord.objects.filter(
            agreement__room__property_id__in=property_ids,
            agreement__tenant__owner=owner,
            billing_month__gte=start_date,
            billing_month__lte=end_date,
        )

        electricity_bills = ElectricityBill.objects.filter(
            meter__room__property_id__in=property_ids,
            billing_month__gte=start_date,
            billing_month__lte=end_date,
        )

        payments = Payment.objects.filter(
            agreement__room__property_id__in=property_ids,
            agreement__tenant__owner=owner,
            status="COMPLETED",
            payment_date__date__gte=start_date,
            payment_date__date__lte=end_date,
        )

        rent_payments = payments.filter(
            rent_record__isnull=False,
        )

        electricity_payments = payments.filter(
            electricity_bill__isnull=False,
        )

        rent_collected_payments = (
            rent_payments.aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )

        rent_collected_records = (
            rent_records.aggregate(total=Sum("amount_paid"))["total"]
            or Decimal("0.00")
        )

        rent_collected = max(rent_collected_payments, rent_collected_records)

        electricity_collected = (
            electricity_payments.aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )

        total_collected = rent_collected + electricity_collected

        rent_due = sum(
            (
                max(
                    Decimal("0.00"),
                    record.rent_amount - record.amount_paid,
                )
                for record in rent_records
            ),
            Decimal("0.00"),
        )

        electricity_due = sum(
            (
                max(
                    Decimal("0.00"),
                    bill.total_amount - bill.amount_paid,
                )
                for bill in electricity_bills
            ),
            Decimal("0.00"),
        )

        total_rooms = rooms.count()
        occupied_rooms = rooms.filter(status="OCCUPIED").count()
        vacant_rooms = rooms.filter(status="VACANT").count()
        maintenance_rooms = rooms.filter(status="MAINTENANCE").count()

        occupancy_rate = (
            round(occupied_rooms / total_rooms * 100, 1)
            if total_rooms
            else 0
        )

        monthly_income = []

        for month in month_range(start_date, end_date):
            month_rent_records = rent_records.filter(
                billing_month__year=month.year,
                billing_month__month=month.month,
            )

            month_payments = rent_payments.filter(
                payment_date__year=month.year,
                payment_date__month=month.month,
            )

            expected = (
                month_rent_records.aggregate(
                    total=Sum("rent_amount")
                )["total"]
                or Decimal("0.00")
            )

            collected_payments = (
                month_payments.aggregate(
                    total=Sum("amount")
                )["total"]
                or Decimal("0.00")
            )

            collected_records = (
                month_rent_records.aggregate(
                    total=Sum("amount_paid")
                )["total"]
                or Decimal("0.00")
            )

            collected = max(collected_payments, collected_records)

            monthly_income.append({
                "month": month.strftime("%b"),
                "year": month.year,
                "expected": money(expected),
                "collected": money(collected),
            })

        property_performance = []

        for prop in properties.order_by("name"):
            prop_rent_records = rent_records.filter(
                agreement__room__property=prop,
            )

            prop_rent_payments = rent_payments.filter(
                agreement__room__property=prop,
            )

            expected = (
                prop_rent_records.aggregate(
                    total=Sum("rent_amount")
                )["total"]
                or Decimal("0.00")
            )

            collected_payments = (
                prop_rent_payments.aggregate(
                    total=Sum("amount")
                )["total"]
                or Decimal("0.00")
            )

            collected_records = (
                prop_rent_records.aggregate(
                    total=Sum("amount_paid")
                )["total"]
                or Decimal("0.00")
            )

            collected = max(collected_payments, collected_records)

            pending = sum(
                (
                    max(
                        Decimal("0.00"),
                        record.rent_amount - record.amount_paid,
                    )
                    for record in prop_rent_records
                ),
                Decimal("0.00"),
            )

            prop_rooms = rooms.filter(property=prop)
            prop_total_rooms = prop_rooms.count()
            prop_occupied = prop_rooms.filter(
                status="OCCUPIED"
            ).count()

            collection_rate = (
                round(float(collected / expected * 100), 1)
                if expected
                else 0
            )

            property_performance.append({
                "property_id": prop.pk,
                "property_name": prop.name,
                "total_rooms": prop_total_rooms,
                "occupied_rooms": prop_occupied,
                "expected_rent": money(expected),
                "collected_rent": money(collected),
                "pending_rent": money(pending),
                "collection_rate": collection_rate,
            })

        return Response({
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "summary": {
                "rent_collected": money(rent_collected),
                "electricity_collected": money(electricity_collected),
                "total_collected": money(total_collected),
                "outstanding_rent": money(rent_due),
                "outstanding_electricity": money(electricity_due),
                "total_outstanding": money(rent_due + electricity_due),
                "total_rooms": total_rooms,
                "occupied_rooms": occupied_rooms,
                "vacant_rooms": vacant_rooms,
                "maintenance_rooms": maintenance_rooms,
                "occupancy_rate": occupancy_rate,
            },
            "monthly_income": monthly_income,
            "property_performance": property_performance,
        })
