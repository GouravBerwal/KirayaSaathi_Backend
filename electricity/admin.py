from django.contrib import admin
from .models import ElectricityMeter, MeterReading, ElectricityBill
# Register your models here.

@admin.register(ElectricityMeter)
class ElectricityMeterAdmin(admin.ModelAdmin):
    list_display = ("meter_number", "room", "installation_date", "is_active")
    list_filter = ("is_active", "installation_date")
    search_fields = ("meter_number", "room__room_number")


@admin.register(MeterReading)
class MeterReadingAdmin(admin.ModelAdmin):
    list_display = (
        "meter",
        "reading_date",
        "previous_reading",
        "current_reading",
    )
    list_filter = ("reading_date",)
    search_fields = ("meter__meter_number",)


@admin.register(ElectricityBill)
class ElectricityBillAdmin(admin.ModelAdmin):
    list_display = (
        "meter",
        "billing_month",
        "units_consumed",
        "total_amount",
        "amount_paid",
        "status",
    )
    list_filter = ("status", "billing_month")
    search_fields = ("meter__meter_number",)
