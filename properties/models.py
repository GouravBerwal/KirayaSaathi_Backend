
import builtins
from django.conf import settings
from django.db import models


class Property(models.Model):
    # Each property belongs to one owner account.
    # Protect rental records from accidental owner deletion.
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_properties",
    )

    PROPERTY_TYPES = [
        ("HOSTEL", "Hostel"),
        ("PG", "PG / Co-Living"),
        ("APARTMENT", "Apartment"),
        ("BUILDING", "Building / Residential"),
        ("HOUSE", "House / Independent"),
        ("COMMERCIAL", "Commercial Property"),
        ("OTHER", "Other"),
    ]

    name = models.CharField(max_length=150)
    property_type = models.CharField(
        max_length=20,
        choices=PROPERTY_TYPES,
        default="BUILDING",
    )
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pin_code = models.CharField(max_length=10)

    monthly_rent = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    security_deposit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    rent_due_day = models.PositiveSmallIntegerField(default=5)
    electricity_rate = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    image = models.ImageField(
        upload_to="properties/",
        blank=True,
        null=True,
    )
    owner_display_name = models.CharField(max_length=150, blank=True, default="")
    contact_number = models.CharField(max_length=20, blank=True, default="")

    def __str__(self):
        return self.name


class Room(models.Model):
    ROOM_TYPES = [
        ("SINGLE", "Single"),
        ("DOUBLE", "Double"),
        ("TRIPLE", "Triple"),
        ("FOUR", "Four Sharing"),
        ("SHARED", "Shared"),
    ]

    ROOM_STATUSES = [
        ("VACANT", "Vacant"),
        ("OCCUPIED", "Occupied"),
        ("MAINTENANCE", "Maintenance"),
    ]

    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name="rooms",
    )

    room_number = models.CharField(max_length=30)
    floor = models.CharField(max_length=50, blank=True)

    room_type = models.CharField(
        max_length=20,
        choices=ROOM_TYPES,
        default="SINGLE",
    )

    monthly_rent = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    security_deposit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    status = models.CharField(
        max_length=20,
        choices=ROOM_STATUSES,
        default="VACANT",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @builtins.property
    def capacity(self):
        t = str(self.room_type).strip().upper()
        if "SINGLE" in t or "1 BHK" in t or "STUDIO" in t:
            return 1
        if "DOUBLE" in t or "TWIN" in t or "2" in t:
            return 2
        if "TRIPLE" in t or "3" in t:
            return 3
        if "FOUR" in t or "SHARED" in t or "4" in t:
            return 4
        return 1

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["property", "room_number"],
                name="unique_room_number_per_property",
            )
        ]

    def __str__(self):
        return f"{self.property.name} - Room {self.room_number}"


class WorkspaceSettings(models.Model):
    # Each authenticated user has their own workspace settings.
    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="workspace_settings",
    )

    data = models.JSONField(
        default=dict,
        blank=True,
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "workspace_settings"
        verbose_name = "Workspace Settings"
        verbose_name_plural = "Workspace Settings"

    def __str__(self):
        return f"Settings for {self.owner}"
