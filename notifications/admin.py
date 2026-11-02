
from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "tenant",
        "notification_type",
        "due_date",
        "amount_due",
        "is_read",
        "created_at",
    )

    list_filter = (
        "notification_type",
        "is_read",
        "due_date",
    )

    search_fields = (
        "tenant__full_name",
        "title",
        "message",
    )

    readonly_fields = (
        "created_at",
        "read_at",
    )
