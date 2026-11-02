from django.contrib import admin

from .models import Property, Room


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = (
        "name", "owner", "property_type", "city", "state", "monthly_rent",
    )
    list_filter = ("owner", "property_type", "city", "state")
    list_editable = ("owner",)
    search_fields = ("name", "city", "address", "owner__username")


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("room_number", "property", "room_type", "monthly_rent", "status")
    list_filter = ("room_type", "status", "property")
    search_fields = ("room_number", "property__name")
