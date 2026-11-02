from decimal import Decimal
from django.db import transaction
from django.db.models import Sum
from rest_framework import serializers

from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    property_id = serializers.SerializerMethodField()
    property_name = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = "__all__"
        read_only_fields = ("created_at",)

    def get_property_id(self, obj):
        try:
            if obj.agreement and obj.agreement.room and obj.agreement.room.property:
                return obj.agreement.room.property.id
        except Exception:
            pass
        return None

    def get_property_name(self, obj):
        try:
            if obj.agreement and obj.agreement.room and obj.agreement.room.property:
                return obj.agreement.room.property.name
        except Exception:
            pass
        return None

    def validate(self, attrs):
        agreement = attrs.get(
            "agreement",
            getattr(self.instance, "agreement", None),
        )

        rent_record = attrs.get(
            "rent_record",
            getattr(self.instance, "rent_record", None),
        )

        electricity_bill = attrs.get(
            "electricity_bill",
            getattr(self.instance, "electricity_bill", None),
        )

        amount = attrs.get(
            "amount",
            getattr(self.instance, "amount", None),
        )

        status = attrs.get(
            "status",
            getattr(self.instance, "status", "COMPLETED"),
        )

        request = self.context.get("request")
        if request is not None and request.user.is_authenticated:
            owner_id = request.user.pk
            if agreement is not None and agreement.room.property.owner_id != owner_id:
                raise serializers.ValidationError({
                    "agreement": "Selected agreement is not available to this owner."
                })
            if rent_record is not None and rent_record.agreement.room.property.owner_id != owner_id:
                raise serializers.ValidationError({
                    "rent_record": "Selected rent record is not available to this owner."
                })
            if electricity_bill is not None and electricity_bill.meter.room.property.owner_id != owner_id:
                raise serializers.ValidationError({
                    "electricity_bill": "Selected electricity bill is not available to this owner."
                })

        # Exactly one bill must be selected.
        if (rent_record is None) == (electricity_bill is None):
            raise serializers.ValidationError(
                "Select either a rent record or an electricity bill, not both."
            )

        # Payment amount must be positive.
        if amount is not None and amount <= 0:
            raise serializers.ValidationError({
                "amount": "Payment amount must be greater than zero."
            })

        # Rent record must belong to the selected agreement.
        if rent_record is not None:
            if agreement is None:
                raise serializers.ValidationError({
                    "agreement": "An agreement is required for rent payments."
                })

            if rent_record.agreement_id != agreement.pk:
                raise serializers.ValidationError({
                    "rent_record": "This rent record belongs to another agreement."
                })

        # Electricity bill must belong to the agreement's room.
        if electricity_bill is not None:
            if agreement is None:
                raise serializers.ValidationError({
                    "agreement": (
                        "An agreement is required for electricity payments."
                    )
                })

            if electricity_bill.meter.room_id != agreement.room_id:
                raise serializers.ValidationError({
                    "electricity_bill": (
                        "This electricity bill belongs to another room."
                    )
                })

        # Do not allow a completed payment to exceed the remaining balance.
        if amount is not None and status == "COMPLETED":
            if rent_record is not None:
                total_due = rent_record.rent_amount
                payments = Payment.objects.filter(
                    rent_record=rent_record,
                    status="COMPLETED",
                )
            else:
                total_due = electricity_bill.total_amount
                payments = Payment.objects.filter(
                    electricity_bill=electricity_bill,
                    status="COMPLETED",
                )

            # Exclude this payment when updating an existing payment.
            if self.instance is not None:
                payments = payments.exclude(pk=self.instance.pk)

            already_paid = payments.aggregate(
                total=Sum("amount")
            )["total"] or Decimal("0.00")

            if already_paid + amount > total_due:
                raise serializers.ValidationError({
                    "amount": (
                        "Payment exceeds the remaining bill balance. "
                        f"Remaining balance: {total_due - already_paid}."
                    )
                })

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        payment = Payment.objects.create(**validated_data)

        if payment.status == "COMPLETED":
            # Auto-update linked RentRecord amount_paid and status
            if payment.rent_record:
                rent_rec = payment.rent_record
                rent_rec.amount_paid = (rent_rec.amount_paid or Decimal("0.00")) + payment.amount
                if rent_rec.amount_paid >= rent_rec.rent_amount:
                    rent_rec.status = "PAID"
                elif rent_rec.amount_paid > Decimal("0.00"):
                    rent_rec.status = "PARTIAL"
                rent_rec.save(update_fields=["amount_paid", "status", "updated_at"])

            # Auto-update linked ElectricityBill amount_paid and status
            if payment.electricity_bill:
                elec_bill = payment.electricity_bill
                elec_bill.amount_paid = (elec_bill.amount_paid or Decimal("0.00")) + payment.amount
                if elec_bill.amount_paid >= elec_bill.total_amount:
                    elec_bill.status = "PAID"
                elif elec_bill.amount_paid > Decimal("0.00"):
                    elec_bill.status = "PARTIAL"
                elec_bill.save(update_fields=["amount_paid", "status", "updated_at"])

        return payment
