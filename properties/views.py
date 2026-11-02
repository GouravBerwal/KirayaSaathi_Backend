
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsVerifiedOwner
from config.api_utils import safe_delete

from .models import Property, Room, WorkspaceSettings
from .serializers import (
    PropertySerializer,
    RoomSerializer,
    WorkspaceSettingsSerializer,
)


DEFAULT_SETTINGS = {
    "fullName": "",
    "mobile": "",
    "email": "",
    "address": "",
    "workspaceName": "",
    "language": "English (India)",
    "currency": "INR · Indian Rupee (₹)",
    "timezone": "Asia/Kolkata · IST (UTC+05:30)",
    "dateFormat": "DD MMM YYYY",
    "financialYear": "April – March",
    "whatsappReminders": True,
    "weeklySummary": True,
    "productUpdates": False,
    "defaultRentDueDay": "5th of each month",
    "defaultRate": "8.00",
    "defaultDeposit": "2 months' rent",
    "defaultReminderTiming": "3 days before due date",
    "twoFactor": False,
    "qrConfigs": [],
    "tenantQrMap": {},
}


class PropertyListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = PropertySerializer

    def get_queryset(self):
        return Property.objects.filter(
            owner=self.request.user
        ).order_by("id")

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class PropertyDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PropertySerializer

    def get_queryset(self):
        return Property.objects.filter(owner=self.request.user)

    def perform_destroy(self, instance):
        safe_delete(instance)


class RoomListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = RoomSerializer

    def get_queryset(self):
        return Room.objects.filter(
            property__owner=self.request.user
        ).select_related("property").order_by("id")


class RoomDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = RoomSerializer

    def get_queryset(self):
        return Room.objects.filter(
            property__owner=self.request.user
        ).select_related("property")

    def perform_destroy(self, instance):
        safe_delete(instance)


class WorkspaceSettingsView(APIView):
    permission_classes = [IsVerifiedOwner]

    def get_settings(self, user):
        settings_obj, _ = WorkspaceSettings.objects.get_or_create(
            owner=user,
            defaults={"data": DEFAULT_SETTINGS.copy()},
        )

        saved_data = settings_obj.data or {}

        # Existing saved settings ko defaults ke saath merge karo.
        data = {
            **DEFAULT_SETTINGS,
            **saved_data,
        }

        return settings_obj, data

    def get(self, request):
        settings_obj, data = self.get_settings(request.user)

        return Response({
            "data": data,
            "updated_at": settings_obj.updated_at,
        })

    def put(self, request):
        incoming_data = request.data.get("data")

        if not isinstance(incoming_data, dict):
            return Response(
                {
                    "error": (
                        "The 'data' field must contain "
                        "a valid JSON object."
                    )
                },
                status=400,
            )

        settings_obj, current_data = self.get_settings(request.user)

        # Sirf provided settings update hon; baaki preserve rahen.
        updated_data = {
            **current_data,
            **incoming_data,
        }

        serializer = WorkspaceSettingsSerializer(
            settings_obj,
            data={"data": updated_data},
            partial=True,
            context={"request": request},
        )

        # Serializer validation ko intentionally preserve kiya gaya hai.
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            "message": "Settings saved successfully.",
            "data": serializer.data["data"],
            "updated_at": serializer.data["updated_at"],
        })
