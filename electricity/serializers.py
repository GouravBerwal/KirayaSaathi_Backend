from decimal import Decimal, ROUND_HALF_UP

from rest_framework import serializers

from .models import ElectricityMeter, MeterReading, ElectricityBill
from .services import calculate_electricity_due_date


class ElectricityMeterSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElectricityMeter
        fields = "__all__"
        read_only_fields = ("created_at", "updated_at")

    def validate(self, attrs):
        room = attrs.get("room", getattr(self.instance, "room", None))
        request = self.context.get("request")
        if request and request.user.is_authenticated and room:
            if room.property.owner_id != request.user.pk:
                raise serializers.ValidationError({
                    "room": "Selected room is not available to this owner."
                })
        if self.instance is not None and self.instance.readings.exists():
            if room is not None and room.pk != self.instance.room_id:
                raise serializers.ValidationError({
                    "room": "A meter with readings cannot be moved to another room."
                })
            number = attrs.get("meter_number", self.instance.meter_number)
            if number != self.instance.meter_number:
                raise serializers.ValidationError({
                    "meter_number": "A meter with readings cannot be renumbered."
                })
        return attrs


class MeterReadingSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeterReading
        fields = "__all__"
        read_only_fields = ("created_at",)

    def validate(self, attrs):
        meter = attrs.get("meter", getattr(self.instance, "meter", None))
        reading_date = attrs.get(
            "reading_date", getattr(self.instance, "reading_date", None)
        )
        previous_reading = attrs.get(
            "previous_reading", getattr(self.instance, "previous_reading", None)
        )
        current_reading = attrs.get(
            "current_reading", getattr(self.instance, "current_reading", None)
        )
        request = self.context.get("request")

        # Auto-populate previous_reading from latest meter reading if not provided
        if self.instance is None and meter and (previous_reading is None or previous_reading == 0):
            last_reading = (
                MeterReading.objects
                .filter(meter=meter)
                .order_by("-reading_date")
                .first()
            )
            if last_reading:
                previous_reading = last_reading.current_reading
                attrs["previous_reading"] = previous_reading

        if meter and not meter.is_active:
            raise serializers.ValidationError({
                "meter": "An inactive meter cannot accept a reading."
            })
        if request and request.user.is_authenticated and meter:
            if meter.room.property.owner_id != request.user.pk:
                raise serializers.ValidationError({
                    "meter": "Selected meter is not available to this owner."
                })
        if previous_reading is not None and previous_reading < 0:
            raise serializers.ValidationError({
                "previous_reading": "Reading cannot be negative."
            })
        if current_reading is not None and current_reading < 0:
            raise serializers.ValidationError({
                "current_reading": "Reading cannot be negative."
            })
        if (
            previous_reading is not None
            and current_reading is not None
            and current_reading < previous_reading
        ):
            raise serializers.ValidationError({
                "current_reading": "Current reading cannot be lower than previous reading."
            })
        if self.instance is not None and self.instance.bills.exists():
            protected_fields = {
                "meter": meter.pk if meter else None,
                "reading_date": reading_date,
                "previous_reading": previous_reading,
                "current_reading": current_reading,
            }
            original_values = {
                "meter": self.instance.meter_id,
                "reading_date": self.instance.reading_date,
                "previous_reading": self.instance.previous_reading,
                "current_reading": self.instance.current_reading,
            }
            changed_fields = [
                key for key, value in protected_fields.items()
                if value != original_values[key]
            ]
            if changed_fields:
                raise serializers.ValidationError({
                    "detail": "A reading used by an electricity bill cannot have its meter/date/values changed."
                })

        if meter and reading_date:
            existing = MeterReading.objects.filter(
                meter=meter, reading_date=reading_date
            )
            if self.instance:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise serializers.ValidationError({
                    "reading_date": "A reading already exists for this meter and date."
                })
        return attrs


class ElectricityBillSerializer(serializers.ModelSerializer):
    property_id = serializers.SerializerMethodField()
    property_name = serializers.SerializerMethodField()
    room_id = serializers.SerializerMethodField()
    room_number = serializers.SerializerMethodField()
    room_type = serializers.SerializerMethodField()
    split_count = serializers.SerializerMethodField()
    split_amount = serializers.SerializerMethodField()
    split_units = serializers.SerializerMethodField()
    occupants = serializers.SerializerMethodField()

    class Meta:
        model = ElectricityBill
        fields = "__all__"
        read_only_fields = (
            "created_at", "updated_at",
        )

    def get_property_id(self, obj):
        try:
            if obj.meter and obj.meter.room and obj.meter.room.property:
                return obj.meter.room.property.id
        except Exception:
            pass
        return None

    def get_property_name(self, obj):
        try:
            if obj.meter and obj.meter.room and obj.meter.room.property:
                return obj.meter.room.property.name
        except Exception:
            pass
        return None

    def get_room_id(self, obj):
        try:
            return obj.meter.room.id
        except Exception:
            return None

    def get_room_number(self, obj):
        try:
            return obj.meter.room.room_number
        except Exception:
            return None

    def get_room_type(self, obj):
        try:
            return obj.meter.room.room_type
        except Exception:
            return None

    def _get_active_agreements(self, obj):
        try:
            return list(obj.meter.room.rental_agreements.filter(status="ACTIVE").select_related("tenant"))
        except Exception:
            return []

    def get_occupants(self, obj):
        agreements = self._get_active_agreements(obj)
        return [
            {
                "id": ag.tenant.id,
                "name": ag.tenant.full_name,
                "phone": ag.tenant.phone,
                "email": ag.tenant.email,
                "agreement_id": ag.id,
            }
            for ag in agreements
        ]

    def get_split_count(self, obj):
        agreements = self._get_active_agreements(obj)
        return max(1, len(agreements))

    def get_split_amount(self, obj):
        try:
            count = self.get_split_count(obj)
            return round(float(obj.total_amount) / count, 2)
        except Exception:
            return float(obj.total_amount or 0)

    def get_split_units(self, obj):
        try:
            count = self.get_split_count(obj)
            return round(float(obj.units_consumed) / count, 2)
        except Exception:
            return float(obj.units_consumed or 0)

    def validate(self, attrs):
        meter = attrs.get("meter", getattr(self.instance, "meter", None))
        reading = attrs.get("reading", getattr(self.instance, "reading", None))
        request = self.context.get("request")

        if meter and reading and reading.meter_id != meter.pk:
            raise serializers.ValidationError({
                "reading": "The reading must belong to the selected meter."
            })
        billing_month = attrs.get(
            "billing_month", getattr(self.instance, "billing_month", None)
        )
        due_date = attrs.get("due_date", getattr(self.instance, "due_date", None))
        if billing_month and billing_month.day != 1:
            raise serializers.ValidationError({
                "billing_month": "Use the first day of the billing month (YYYY-MM-01)."
            })
        if meter and billing_month and due_date:
            expected_due_date = calculate_electricity_due_date(
                billing_month, meter.room.property.rent_due_day
            )
            if due_date != expected_due_date:
                raise serializers.ValidationError({
                    "due_date": "Due date must follow the property's configured rent due day."
                })
        if reading is not None:
            existing_bills = ElectricityBill.objects.filter(reading=reading)
            if self.instance is not None:
                existing_bills = existing_bills.exclude(pk=self.instance.pk)
            if existing_bills.exists():
                raise serializers.ValidationError({
                    "reading": "A bill already exists for this reading."
                })
        if request and request.user.is_authenticated and meter:
            if meter.room.property.owner_id != request.user.pk:
                raise serializers.ValidationError({
                    "meter": "Selected meter is not available to this owner."
                })
            if reading and reading.meter.room.property.owner_id != request.user.pk:
                raise serializers.ValidationError({
                    "reading": "Selected reading is not available to this owner."
                })

        # Validate the financial calculation so API clients cannot submit a
        # bill for another number of units or an arbitrary total.
        units = attrs.get("units_consumed", getattr(self.instance, "units_consumed", None))
        rate = attrs.get("rate_per_unit", getattr(self.instance, "rate_per_unit", None))
        total = attrs.get("total_amount", getattr(self.instance, "total_amount", None))
        if reading and units is not None:
            expected_units = reading.current_reading - reading.previous_reading
            if units != expected_units:
                raise serializers.ValidationError({
                    "units_consumed": "Units must equal current reading minus previous reading."
                })
        if meter and rate is not None and rate != meter.room.property.electricity_rate:
            raise serializers.ValidationError({
                "rate_per_unit": "Rate must match the property's configured electricity rate."
            })
        if units is not None and rate is not None and total is not None:
            expected_total = (units * rate).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            if total != expected_total:
                raise serializers.ValidationError({
                    "total_amount": "Total must equal units consumed multiplied by rate per unit."
                })
        return attrs
