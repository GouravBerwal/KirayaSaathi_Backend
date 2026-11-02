from django.contrib import admin

from .models import Tenant, RentalAgreement


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("full_name", "owner", "phone", "email", "created_at")
    list_filter = ("owner",)
    list_editable = ("owner",)
    search_fields = ("full_name", "phone", "email", "owner__username")


@admin.register(RentalAgreement)
class RentalAgreementAdmin(admin.ModelAdmin):
    list_display = ("tenant", "room", "start_date", "end_date", "monthly_rent", "status")
    list_filter = ("status", "start_date")
    search_fields = ("tenant__full_name", "room__room_number", "room__property__name")
