from rest_framework import serializers

from .models import Property, Room, WorkspaceSettings


class PropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = "__all__"
        read_only_fields = (
            "owner",
            "created_at",
            "updated_at",
        )

    def validate_property_type(self, value):
        if not value:
            return "BUILDING"
        val = str(value).strip().upper()
        mapping = {
            "APARTMENT": "APARTMENT",
            "FLAT": "APARTMENT",
            "RESIDENTIAL": "BUILDING",
            "RESIDENTIAL BUILDING": "BUILDING",
            "BUILDING": "BUILDING",
            "HOSTEL": "HOSTEL",
            "PG": "PG",
            "PG / HOSTEL": "HOSTEL",
            "PG / CO-LIVING": "PG",
            "HOUSE": "HOUSE",
            "INDEPENDENT": "HOUSE",
            "INDEPENDENT HOUSE": "HOUSE",
            "COMMERCIAL": "COMMERCIAL",
            "COMMERCIAL PROPERTY": "COMMERCIAL",
            "OTHER": "OTHER",
        }
        if val in mapping:
            return mapping[val]
        valid_keys = dict(Property.PROPERTY_TYPES).keys()
        if val in valid_keys:
            return val
        return "BUILDING"


class RoomSerializer(serializers.ModelSerializer):
    capacity = serializers.SerializerMethodField()
    occupied_beds = serializers.SerializerMethodField()
    vacant_beds = serializers.SerializerMethodField()
    is_full = serializers.SerializerMethodField()
    occupants = serializers.SerializerMethodField()
    tenants = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = "__all__"
        read_only_fields = (
            "created_at",
            "updated_at",
        )

    def get_capacity(self, obj):
        return obj.capacity

    def get_occupied_beds(self, obj):
        try:
            return obj.rental_agreements.filter(status="ACTIVE").count()
        except Exception:
            return 0

    def get_vacant_beds(self, obj):
        occupied = self.get_occupied_beds(obj)
        return max(0, obj.capacity - occupied)

    def get_is_full(self, obj):
        return self.get_occupied_beds(obj) >= obj.capacity

    def get_occupants(self, obj):
        try:
            active_agreements = obj.rental_agreements.filter(status="ACTIVE").select_related("tenant")
            return [
                {
                    "id": str(ag.tenant.id),
                    "name": ag.tenant.full_name,
                    "phone": ag.tenant.phone,
                    "email": ag.tenant.email,
                    "agreement_id": ag.id,
                    "monthly_rent": float(ag.monthly_rent),
                    "move_in_date": str(ag.start_date) if ag.start_date else None,
                }
                for ag in active_agreements
            ]
        except Exception:
            return []

    def get_tenants(self, obj):
        return self.get_occupants(obj)

    def validate_room_type(self, value):
        if not value:
            return "SINGLE"
        val = str(value).strip().upper()
        if "DOUBLE" in val or "TWIN" in val:
            return "DOUBLE"
        if "TRIPLE" in val:
            return "TRIPLE"
        if "FOUR" in val:
            return "FOUR"
        if "SHARED" in val or "DORM" in val or "HALL" in val:
            return "SHARED"
        if val in dict(Room.ROOM_TYPES):
            return val
        return "SINGLE"

    def validate_status(self, value):
        if not value:
            return "VACANT"
        val = str(value).strip().upper()
        if val in dict(Room.ROOM_STATUSES):
            return val
        return "VACANT"

    def validate_property(self, value):
        request = self.context.get("request")

        if request and request.user.is_authenticated:
            if value.owner_id != request.user.pk:
                raise serializers.ValidationError(
                    "Selected property is not available to this owner."
                )

        return value


class WorkspaceSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkspaceSettings
        fields = ["data", "updated_at"]
        read_only_fields = ["updated_at"]

    def validate_data(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError(
                "Settings must be a valid JSON object."
            )

        allowed_fields = {
            "fullName",
            "mobile",
            "email",
            "address",
            "workspaceName",
            "language",
            "currency",
            "timezone",
            "dateFormat",
            "financialYear",
            "whatsappReminders",
            "weeklySummary",
            "productUpdates",
            "defaultRentDueDay",
            "defaultRate",
            "defaultDeposit",
            "defaultReminderTiming",
            "twoFactor",
        }

        unknown_fields = set(value.keys()) - allowed_fields

        if unknown_fields:
            raise serializers.ValidationError(
                "Unsupported settings fields: "
                + ", ".join(sorted(unknown_fields))
            )

        boolean_fields = {
            "whatsappReminders",
            "weeklySummary",
            "productUpdates",
            "twoFactor",
        }

        for field in boolean_fields:
            if field in value and not isinstance(value[field], bool):
                raise serializers.ValidationError({
                    field: "This field must be true or false."
                })

        return value