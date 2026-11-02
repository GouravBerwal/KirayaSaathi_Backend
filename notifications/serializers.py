from django.utils import timezone
from rest_framework import serializers

from .models import Notification
from .message_service import generate_whatsapp_url, format_notification_text, get_notification_context


class NotificationSerializer(serializers.ModelSerializer):
    tenant_name = serializers.CharField(
        source="tenant.full_name",
        read_only=True,
    )
    tenant_phone = serializers.CharField(
        source="tenant.phone",
        read_only=True,
    )
    tenant_email = serializers.CharField(
        source="tenant.email",
        read_only=True,
    )
    whatsapp_url = serializers.SerializerMethodField()
    formatted_message = serializers.SerializerMethodField()
    property_name = serializers.SerializerMethodField()
    room_number = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "tenant",
            "tenant_name",
            "tenant_phone",
            "tenant_email",
            "property_name",
            "room_number",
            "rent_record",
            "electricity_bill",
            "notification_type",
            "title",
            "message",
            "formatted_message",
            "whatsapp_url",
            "due_date",
            "amount_due",
            "is_read",
            "read_at",
            "is_sent",
            "sent_at",
            "sent_via",
            "delivery_status",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "tenant",
            "tenant_name",
            "tenant_phone",
            "tenant_email",
            "property_name",
            "room_number",
            "rent_record",
            "electricity_bill",
            "notification_type",
            "title",
            "message",
            "formatted_message",
            "whatsapp_url",
            "due_date",
            "amount_due",
            "read_at",
            "is_sent",
            "sent_at",
            "sent_via",
            "delivery_status",
            "created_at",
        ]

    def get_whatsapp_url(self, obj):
        return generate_whatsapp_url(obj)

    def get_formatted_message(self, obj):
        return format_notification_text(obj)

    def get_property_name(self, obj):
        ctx = get_notification_context(obj)
        return ctx.get("property_name", "")

    def get_room_number(self, obj):
        ctx = get_notification_context(obj)
        return ctx.get("room_number", "")

    def update(self, instance, validated_data):
        is_read = validated_data.get(
            "is_read",
            instance.is_read,
        )

        if is_read and not instance.is_read:
            instance.read_at = timezone.now()
        elif not is_read:
            instance.read_at = None

        instance.is_read = is_read
        instance.save(update_fields=["is_read", "read_at"])
        return instance
