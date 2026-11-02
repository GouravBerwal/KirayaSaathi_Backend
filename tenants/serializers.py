
from rest_framework import serializers

from .models import Tenant, RentalAgreement


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = "__all__"
        read_only_fields = (
            "owner",
            "created_at",
            "updated_at",
        )


class RentalAgreementSerializer(serializers.ModelSerializer):
    property_id = serializers.IntegerField(
        source="room.property.id",
        read_only=True,
    )
    property_name = serializers.CharField(
        source="room.property.name",
        read_only=True,
    )
    tenant_name = serializers.CharField(
        source="tenant.full_name",
        read_only=True,
    )
    room_number = serializers.CharField(
        source="room.room_number",
        read_only=True,
    )
    room_type = serializers.CharField(
        source="room.room_type",
        read_only=True,
    )
    room_capacity = serializers.IntegerField(
        source="room.capacity",
        read_only=True,
    )
    tenant_phone = serializers.CharField(
        source="tenant.phone",
        read_only=True,
    )

    class Meta:
        model = RentalAgreement
        fields = "__all__"
        read_only_fields = (
            "created_at",
            "updated_at",
        )

    def validate(self, attrs):
        request = self.context.get("request")

        # Current tenant and room, including existing values during updates.
        tenant = attrs.get(
            "tenant",
            getattr(self.instance, "tenant", None),
        )
        room = attrs.get(
            "room",
            getattr(self.instance, "room", None),
        )

        # Verify ownership for authenticated requests.
        if request and request.user.is_authenticated:
            owner_id = request.user.pk

            if tenant is not None and tenant.owner_id != owner_id:
                raise serializers.ValidationError({
                    "tenant": (
                        "Selected tenant is not available to this owner."
                    )
                })

            if room is not None and room.property.owner_id != owner_id:
                raise serializers.ValidationError({
                    "room": (
                        "Selected room is not available to this owner."
                    )
                })

            if (
                tenant is not None
                and room is not None
                and tenant.owner_id != room.property.owner_id
            ):
                raise serializers.ValidationError(
                    "Tenant and room must belong to the same owner."
                )

        return attrs
