
from rest_framework import serializers

from .models import (
    RentRecord,
    BillingArchive,
    OwnerQrConfig,
    TenantQrAssignment,
)


class RentRecordSerializer(serializers.ModelSerializer):
    tenant_name = serializers.CharField(
        source="agreement.tenant.full_name",
        read_only=True,
    )
    tenant_id = serializers.IntegerField(
        source="agreement.tenant.id",
        read_only=True,
    )
    tenant_phone = serializers.CharField(
        source="agreement.tenant.phone",
        read_only=True,
        default="",
    )
    property_id = serializers.IntegerField(
        source="agreement.room.property.id",
        read_only=True,
    )
    property_name = serializers.CharField(
        source="agreement.room.property.name",
        read_only=True,
    )
    room_number = serializers.CharField(
        source="agreement.room.room_number",
        read_only=True,
    )
    room_type = serializers.CharField(
        source="agreement.room.room_type",
        read_only=True,
    )
    room_capacity = serializers.IntegerField(
        source="agreement.room.capacity",
        read_only=True,
    )
    outstanding_amount = serializers.SerializerMethodField()

    class Meta:
        model = RentRecord
        fields = "__all__"
        read_only_fields = (
            "created_at",
            "updated_at",
            "archived_at",
        )

    def get_outstanding_amount(self, obj):
        outstanding = obj.rent_amount - obj.amount_paid
        return str(max(outstanding, 0))

    def validate(self, attrs):
        agreement = attrs.get(
            "agreement",
            getattr(self.instance, "agreement", None),
        )
        request = self.context.get("request")

        if (
            agreement is not None
            and request is not None
            and request.user.is_authenticated
            and agreement.room.property.owner_id
            != request.user.pk
        ):
            raise serializers.ValidationError({
                "agreement": (
                    "Selected agreement is not available "
                    "to this owner."
                )
            })

        amount = attrs.get(
            "rent_amount",
            getattr(self.instance, "rent_amount", None),
        )

        if amount is not None and amount < 0:
            raise serializers.ValidationError({
                "rent_amount": "Rent amount cannot be negative."
            })

        return attrs


class BillingArchiveSerializer(serializers.ModelSerializer):
    property_name = serializers.CharField(
        source="property.name",
        read_only=True,
        default="All Properties",
    )
    billing_month_formatted = serializers.SerializerMethodField()

    class Meta:
        model = BillingArchive
        fields = [
            "id",
            "billing_month",
            "billing_month_formatted",
            "property",
            "property_name",
            "total_tenants",
            "total_billed",
            "total_paid",
            "total_balance",
            "archived_at",
            "snapshot_data",
            "notes",
        ]
        read_only_fields = ["id", "archived_at"]

    def get_billing_month_formatted(self, obj):
        return obj.billing_month.strftime("%B %Y")


class OwnerQrConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = OwnerQrConfig
        fields = [
            "id",
            "label",
            "payee_name",
            "upi_id",
            "qr_image_data_url",
            "property_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]

    def validate_label(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError(
                "QR profile label is required."
            )
        return value

    def validate_payee_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError(
                "Payee name is required."
            )
        return value

    def validate_upi_id(self, value):
        value = value.strip()
        if not value or "@" not in value:
            raise serializers.ValidationError(
                "Enter a valid UPI ID."
            )
        return value

    def validate_qr_image_data_url(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError(
                "Upload your own QR image before saving."
            )

        if not value.startswith("data:image/"):
            raise serializers.ValidationError(
                "QR image must be an uploaded image data URL."
            )

        return value


class TenantQrAssignmentSerializer(serializers.ModelSerializer):
    qr_config_details = OwnerQrConfigSerializer(
        source="qr_config",
        read_only=True,
    )

    class Meta:
        model = TenantQrAssignment
        fields = [
            "id",
            "tenant_id",
            "qr_config",
            "qr_config_details",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]

    def validate_qr_config(self, value):
        request = self.context.get("request")

        if (
            request
            and value.owner_id != request.user.pk
        ):
            raise serializers.ValidationError(
                "You can only assign your own QR profiles."
            )

        return value
