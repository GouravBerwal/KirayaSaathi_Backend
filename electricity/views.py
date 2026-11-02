import uuid
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import generics, status

from config.api_utils import safe_delete
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ElectricityMeter, MeterReading, ElectricityBill
from .serializers import (
    ElectricityMeterSerializer,
    MeterReadingSerializer,
    ElectricityBillSerializer,
)
from .services import generate_electricity_bill


class ElectricityMeterListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = ElectricityMeterSerializer

    def get_queryset(self):
        return ElectricityMeter.objects.filter(
            room__property__owner=self.request.user
        ).select_related("room", "room__property")


class ElectricityMeterDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ElectricityMeterSerializer

    def get_queryset(self):
        return ElectricityMeter.objects.filter(
            room__property__owner=self.request.user
        ).select_related("room", "room__property")

    def perform_destroy(self, instance):
        safe_delete(instance)


class MeterReadingListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = MeterReadingSerializer

    def get_queryset(self):
        return MeterReading.objects.filter(
            meter__room__property__owner=self.request.user
        ).select_related("meter", "meter__room", "meter__room__property")


class MeterReadingDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MeterReadingSerializer

    def get_queryset(self):
        return MeterReading.objects.filter(
            meter__room__property__owner=self.request.user
        ).select_related("meter", "meter__room", "meter__room__property")

    def perform_destroy(self, instance):
        safe_delete(instance)


class ElectricityBillListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = ElectricityBillSerializer

    def get_queryset(self):
        return ElectricityBill.objects.filter(
            meter__room__property__owner=self.request.user
        ).select_related(
            "meter", "reading", "meter__room", "meter__room__property"
        )


class ElectricityBillDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ElectricityBillSerializer

    def get_queryset(self):
        return ElectricityBill.objects.filter(
            meter__room__property__owner=self.request.user
        ).select_related(
            "meter", "reading", "meter__room", "meter__room__property"
        )

    def perform_update(self, serializer):
        with transaction.atomic():
            bill = serializer.save()
            from payments.models import Payment
            status_val = str(bill.status).upper()
            if status_val == "PAID":
                if bill.amount_paid < bill.total_amount:
                    bill.amount_paid = bill.total_amount
                    bill.save(update_fields=["amount_paid", "updated_at"])
                active_ag = bill.meter.room.rental_agreements.filter(status="ACTIVE").first()
                if active_ag:
                    existing_pay = Payment.objects.filter(
                        electricity_bill=bill,
                        status="COMPLETED"
                    ).first()
                    if not existing_pay:
                        Payment.objects.create(
                            agreement=active_ag,
                            electricity_bill=bill,
                            amount=bill.total_amount,
                            payment_date=timezone.now(),
                            payment_method="UPI",
                            status="COMPLETED",
                            transaction_reference=f"CONFIRM-ELEC-{uuid.uuid4().hex[:8].upper()}",
                            notes="Marked Paid by Owner",
                        )
            elif status_val == "PENDING":
                bill.amount_paid = Decimal("0.00")
                bill.save(update_fields=["amount_paid", "updated_at"])
                Payment.objects.filter(electricity_bill=bill, status="COMPLETED").delete()

    def perform_destroy(self, instance):
        safe_delete(instance)


class GenerateElectricityBillAPIView(APIView):
    def post(self, request):
        reading_id = request.data.get("reading_id")
        if reading_id in (None, ""):
            return Response(
                {"error": "reading_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            reading_id = int(reading_id)
            if reading_id < 1:
                raise ValueError
        except (TypeError, ValueError):
            return Response(
                {"error": "reading_id must be a positive integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        billing_month_param = request.data.get("billing_month")
        parsed_billing_month = None
        if billing_month_param:
            try:
                from datetime import date
                if isinstance(billing_month_param, str):
                    parts = [int(p) for p in billing_month_param.split("-")]
                    parsed_billing_month = date(parts[0], parts[1], parts[2] if len(parts) > 2 else 1)
            except Exception:
                parsed_billing_month = None

        try:
            bill, created = generate_electricity_bill(
                reading_id=reading_id,
                billing_month=parsed_billing_month,
                owner=request.user,
            )
        except MeterReading.DoesNotExist:
            raise NotFound("Meter reading was not found.")
        except DjangoValidationError as error:
            raise ValidationError({"error": error.messages})

        response_data = {
            "message": (
                "Electricity bill generated successfully."
                if created else "A bill already exists for this reading."
            ),
            "created": created,
            "bill_id": bill.pk,
            "meter_number": bill.meter.meter_number,
            "billing_month": bill.billing_month.isoformat(),
            "units_consumed": str(bill.units_consumed),
            "rate_per_unit": str(bill.rate_per_unit),
            "total_amount": str(bill.total_amount),
            "due_date": bill.due_date.isoformat(),
            "status": bill.status,
        }
        return Response(
            response_data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
