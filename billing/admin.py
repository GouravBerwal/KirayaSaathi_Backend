from django.contrib import admin
from .models import RentRecord
# Register your models here.

@admin.register(RentRecord)
class RentRecordAdmin(admin.ModelAdmin):
    list_display = (
        "agreement",
        "billing_month",
        "rent_amount",
        "amount_paid",
        "due_date",
        "status",
    )
    list_filter = ("status", "billing_month")
    search_fields = ("agreement__tenant__full_name",)
