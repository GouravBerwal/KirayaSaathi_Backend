from django.db import transaction
from rest_framework import generics
from rest_framework.exceptions import ValidationError

from config.api_utils import safe_delete
from properties.models import Room
from .models import Tenant, RentalAgreement
from .serializers import TenantSerializer, RentalAgreementSerializer


class TenantListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = TenantSerializer

    def get_queryset(self):
        return Tenant.objects.filter(owner=self.request.user).order_by("id")

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class TenantDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TenantSerializer

    def get_queryset(self):
        return Tenant.objects.filter(owner=self.request.user)

    def perform_destroy(self, instance):
        safe_delete(instance)


def validate_room_assignment(room, status, exclude_pk=None):
    if status != "ACTIVE":
        return

    if room.status == "MAINTENANCE":
        raise ValidationError({
            "room": "A room under maintenance cannot be assigned."
        })

    capacity = getattr(room, "capacity", 1)
    active_agreements = RentalAgreement.objects.filter(
        room_id=room.pk,
        status="ACTIVE",
    )
    if exclude_pk is not None:
        active_agreements = active_agreements.exclude(pk=exclude_pk)

    if active_agreements.count() >= capacity:
        room_label = room.get_room_type_display() if hasattr(room, "get_room_type_display") else room.room_type
        raise ValidationError({
            "room": f"Room {room.room_number} ({room_label}) already has {active_agreements.count()} active tenant(s) and has reached its maximum capacity of {capacity} tenant(s)."
        })


class RentalAgreementListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = RentalAgreementSerializer

    def get_queryset(self):
        return RentalAgreement.objects.filter(
            room__property__owner=self.request.user,
            tenant__owner=self.request.user,
        ).select_related("tenant", "room", "room__property")

    def perform_create(self, serializer):
        with transaction.atomic():
            room_id = serializer.validated_data["room"].pk
            room = Room.objects.select_for_update().select_related(
                "property"
            ).get(pk=room_id, property__owner=self.request.user)
            status_value = serializer.validated_data.get("status", "ACTIVE")
            validate_room_assignment(room, status_value)
            serializer.save()

    @staticmethod
    def validate_room_assignment(room, status, exclude_pk=None):
        return validate_room_assignment(room, status, exclude_pk=exclude_pk)


class RentalAgreementDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = RentalAgreementSerializer

    def get_queryset(self):
        return RentalAgreement.objects.filter(
            room__property__owner=self.request.user,
            tenant__owner=self.request.user,
        ).select_related("tenant", "room", "room__property")

    def perform_update(self, serializer):
        with transaction.atomic():
            agreement = serializer.instance
            new_room = serializer.validated_data.get("room", agreement.room)
            new_status = serializer.validated_data.get("status", agreement.status)
            room_ids = sorted({agreement.room_id, new_room.pk})
            locked_rooms = list(
                Room.objects.select_for_update()
                .filter(pk__in=room_ids, property__owner=self.request.user)
                .order_by("pk")
            )
            room_by_id = {room.pk: room for room in locked_rooms}
            if new_room.pk not in room_by_id:
                raise ValidationError({"room": "Selected room is not available to this owner."})
            validate_room_assignment(
                room=room_by_id[new_room.pk],
                status=new_status,
                exclude_pk=agreement.pk,
            )
            serializer.save()

    def perform_destroy(self, instance):
        with transaction.atomic():
            Room.objects.select_for_update().get(
                pk=instance.room_id,
                property__owner=self.request.user,
            )
            safe_delete(instance)


class SecurityDepositListAPIView(generics.ListAPIView):
    serializer_class = RentalAgreementSerializer

    def get_queryset(self):
        qs = RentalAgreement.objects.filter(
            room__property__owner=self.request.user,
            tenant__owner=self.request.user,
        ).select_related("tenant", "room", "room__property").order_by("-start_date", "-id")

        property_id = self.request.query_params.get("property")
        if property_id:
            qs = qs.filter(room__property_id=property_id)

        status_param = self.request.query_params.get("status")
        if status_param and status_param != "ALL":
            qs = qs.filter(security_deposit_status=status_param.upper())

        return qs


class SecurityDepositDetailAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = RentalAgreementSerializer

    def get_queryset(self):
        return RentalAgreement.objects.filter(
            room__property__owner=self.request.user,
            tenant__owner=self.request.user,
        ).select_related("tenant", "room", "room__property")
