from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from rest_framework import generics, serializers

from billing.models import RentRecord
from electricity.models import ElectricityBill
from .models import Payment
from .serializers import PaymentSerializer
from .services import sync_payment_bills


def _validate_locked_payment_balance(validated_data, instance=None):
    """Re-check the remaining balance under a row lock to reduce race risks."""
    rent_record = validated_data.get(
        "rent_record", getattr(instance, "rent_record", None)
    )
    electricity_bill = validated_data.get(
        "electricity_bill", getattr(instance, "electricity_bill", None)
    )
    amount = validated_data.get("amount", getattr(instance, "amount", None))
    status_value = validated_data.get(
        "status", getattr(instance, "status", "COMPLETED")
    )

    if status_value != "COMPLETED" or amount is None:
        return

    if rent_record is not None:
        locked_bill = RentRecord.objects.select_for_update().get(pk=rent_record.pk)
        total_due = locked_bill.rent_amount
        payments = Payment.objects.filter(
            rent_record_id=locked_bill.pk, status="COMPLETED"
        )
    elif electricity_bill is not None:
        locked_bill = ElectricityBill.objects.select_for_update().get(
            pk=electricity_bill.pk
        )
        total_due = locked_bill.total_amount
        payments = Payment.objects.filter(
            electricity_bill_id=locked_bill.pk, status="COMPLETED"
        )
    else:
        return

    if instance is not None:
        payments = payments.exclude(pk=instance.pk)
    paid = payments.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    if total_due > Decimal("0.00") and paid >= total_due:
        raise serializers.ValidationError({
            "amount": f"This bill has already been fully paid (Total: {total_due}, Paid: {paid})."
        })
    # Allow small rounding difference (up to ₹1.00) if amount slightly exceeds remaining
    if paid + amount > total_due and (paid + amount - total_due) > Decimal("1.00"):
        raise serializers.ValidationError({
            "amount": f"Payment exceeds the remaining balance of {total_due - paid}."
        })


class PaymentListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = PaymentSerializer

    def get_queryset(self):
        return Payment.objects.filter(
            agreement__room__property__owner=self.request.user
        ).select_related(
            "agreement",
            "agreement__room__property",
            "agreement__tenant",
            "rent_record",
            "electricity_bill",
        ).order_by("-payment_date", "-id")

    def perform_create(self, serializer):
        with transaction.atomic():
            _validate_locked_payment_balance(serializer.validated_data)
            payment = serializer.save()
            sync_payment_bills(
                rent_record_ids=[payment.rent_record_id] if payment.rent_record_id else [],
                electricity_bill_ids=[payment.electricity_bill_id] if payment.electricity_bill_id else [],
            )


class PaymentDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PaymentSerializer

    def get_queryset(self):
        return Payment.objects.filter(
            agreement__room__property__owner=self.request.user
        ).select_related(
            "agreement", "agreement__room__property", "agreement__tenant",
            "rent_record", "electricity_bill",
        )

    def perform_update(self, serializer):
        with transaction.atomic():
            old_payment = serializer.instance
            old_rent_id = old_payment.rent_record_id
            old_electricity_id = old_payment.electricity_bill_id
            _validate_locked_payment_balance(
                serializer.validated_data, instance=old_payment
            )
            payment = serializer.save()
            sync_payment_bills(
                rent_record_ids=[pk for pk in (old_rent_id, payment.rent_record_id) if pk is not None],
                electricity_bill_ids=[pk for pk in (old_electricity_id, payment.electricity_bill_id) if pk is not None],
            )

    def perform_destroy(self, instance):
        with transaction.atomic():
            rent_id = instance.rent_record_id
            electricity_id = instance.electricity_bill_id
            instance.delete()
            sync_payment_bills(
                rent_record_ids=[rent_id] if rent_id else [],
                electricity_bill_ids=[electricity_id] if electricity_id else [],
            )