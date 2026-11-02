from django.contrib import admin
from .models import Payment

# Register your models here.

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "agreement",
        "amount",
        "payment_date",
        "payment_method",
        "status",
    )

    list_filter = ("status", "payment_method", "payment_date")

    search_fields = (
        "agreement__tenant__full_name",
        "transaction_reference",
    )
