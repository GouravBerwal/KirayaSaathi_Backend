
import csv
import uuid
from decimal import Decimal

from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response

from accounts.permissions import IsVerifiedOwner
from config.api_utils import safe_delete
from tenants.models import RentalAgreement

from .models import (
    RentRecord,
    BillingArchive,
    OwnerQrConfig,
    TenantQrAssignment,
)
from .serializers import (
    RentRecordSerializer,
    BillingArchiveSerializer,
    OwnerQrConfigSerializer,
    TenantQrAssignmentSerializer,
)
from .services import archive_billing_month


class RentRecordListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = RentRecordSerializer
    permission_classes = [IsVerifiedOwner]

    def get_queryset(self):
        qs = RentRecord.objects.filter(
            agreement__room__property__owner=self.request.user
        ).select_related(
            "agreement",
            "agreement__tenant",
            "agreement__room",
            "agreement__room__property",
        )

        is_archived = self.request.query_params.get("archived")
        if is_archived is not None:
            qs = qs.filter(
                is_archived=is_archived.lower() in ["true", "1"]
            )

        return qs


class RentRecordDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = RentRecordSerializer
    permission_classes = [IsVerifiedOwner]

    def get_queryset(self):
        return RentRecord.objects.filter(
            agreement__room__property__owner=self.request.user
        ).select_related(
            "agreement",
            "agreement__tenant",
            "agreement__room",
            "agreement__room__property",
        )

    def perform_update(self, serializer):
        with transaction.atomic():
            record = serializer.save()

            from payments.models import Payment

            status_val = str(record.status).upper()

            if status_val == "PAID":
                if record.amount_paid < record.rent_amount:
                    record.amount_paid = record.rent_amount
                    record.save(
                        update_fields=["amount_paid", "updated_at"]
                    )

                existing_pay = Payment.objects.filter(
                    rent_record=record,
                    status="COMPLETED",
                ).first()

                if not existing_pay:
                    Payment.objects.create(
                        agreement=record.agreement,
                        rent_record=record,
                        amount=record.rent_amount,
                        payment_date=timezone.now(),
                        payment_method="UPI",
                        status="COMPLETED",
                        transaction_reference=(
                            f"CONFIRM-{uuid.uuid4().hex[:8].upper()}"
                        ),
                        notes="Marked Paid by Owner",
                    )

            elif status_val == "PENDING":
                record.amount_paid = Decimal("0.00")
                record.save(
                    update_fields=["amount_paid", "updated_at"]
                )

                Payment.objects.filter(
                    rent_record=record,
                    status="COMPLETED",
                ).delete()

    def perform_destroy(self, instance):
        safe_delete(instance)


class BillingArchiveListCreateAPIView(APIView):
    permission_classes = [IsVerifiedOwner]

    def get(self, request):
        archives = BillingArchive.objects.filter(
            owner=request.user
        ).order_by("-billing_month")

        serializer = BillingArchiveSerializer(
            archives,
            many=True,
        )
        return Response(serializer.data)

    def post(self, request):
        billing_month = request.data.get("billing_month")

        if not billing_month:
            return Response(
                {
                    "error": (
                        "billing_month is required "
                        "(format: YYYY-MM or YYYY-MM-DD)."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        property_id = request.data.get("property_id")
        notes = request.data.get("notes", "")

        try:
            result = archive_billing_month(
                owner=request.user,
                billing_month=billing_month,
                property_id=property_id,
                notes=notes,
            )

            archive = result["archive"]
            serializer = BillingArchiveSerializer(archive)

            return Response(
                {
                    "message": (
                        f"Successfully archived "
                        f"{archive.billing_month.strftime('%B %Y')}!"
                    ),
                    "archive": serializer.data,
                    "records_archived": result["records_archived"],
                    "meters_rolled_over": result["meters_rolled_over"],
                    "next_month": result["next_month"],
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception:
            return Response(
                {
                    "error": (
                        "Could not archive this billing month. "
                        "Check the month format and try again."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


class BillingArchiveDetailAPIView(
    generics.RetrieveUpdateDestroyAPIView
):
    serializer_class = BillingArchiveSerializer
    permission_classes = [IsVerifiedOwner]

    def get_queryset(self):
        return BillingArchive.objects.filter(
            owner=self.request.user
        )


class BillingArchiveDownloadAPIView(APIView):
    permission_classes = [IsVerifiedOwner]

    def get(self, request, pk):
        try:
            archive = BillingArchive.objects.get(
                pk=pk,
                owner=request.user,
            )
        except BillingArchive.DoesNotExist:
            return Response(
                {"error": "Archive not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        month_label = archive.billing_month.strftime("%B_%Y")
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            f'attachment; filename="Billing_Archive_{month_label}.csv"'
        )

        writer = csv.writer(response)
        writer.writerow([
            "Tenant Name",
            "Phone",
            "Property",
            "Room",
            "Billing Month",
            "Due Date",
            "Room Rent (INR)",
            "Rent Paid (INR)",
            "Rent Balance (INR)",
            "Rent Status",
            "Meter No.",
            "Previous Reading",
            "Current Reading",
            "Units Consumed",
            "Rate / Unit",
            "Electricity Amt (INR)",
            "Electricity Paid (INR)",
            "Electricity Status",
            "Total Billed (INR)",
            "Total Paid (INR)",
            "Final Balance (INR)",
        ])

        for item in archive.snapshot_data:
            writer.writerow([
                item.get("tenant_name", ""),
                item.get("tenant_phone", ""),
                item.get("property_name", ""),
                item.get("room_number", ""),
                item.get("billing_month", ""),
                item.get("due_date", ""),
                item.get("rent_amount", "0"),
                item.get("rent_paid", "0"),
                item.get("rent_balance", "0"),
                item.get("rent_status", ""),
                item.get("meter_number", ""),
                item.get("previous_reading", "0"),
                item.get("current_reading", "0"),
                item.get("units_consumed", "0"),
                item.get("rate_per_unit", "0"),
                item.get("electricity_amount", "0"),
                item.get("electricity_paid", "0"),
                item.get("electricity_status", ""),
                item.get("total_billed", "0"),
                item.get("total_paid", "0"),
                item.get("balance", "0"),
            ])

        return response


# ---------------------------------------------------------
# Owner QR profile APIs
# ---------------------------------------------------------

class OwnerQrConfigListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = OwnerQrConfigSerializer
    permission_classes = [IsVerifiedOwner]

    def get_queryset(self):
        return OwnerQrConfig.objects.filter(
            owner=self.request.user
        )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class OwnerQrConfigDetailAPIView(
    generics.RetrieveUpdateDestroyAPIView
):
    serializer_class = OwnerQrConfigSerializer
    permission_classes = [IsVerifiedOwner]

    def get_queryset(self):
        return OwnerQrConfig.objects.filter(
            owner=self.request.user
        )


# ---------------------------------------------------------
# Tenant-specific QR assignment APIs
# ---------------------------------------------------------

class TenantQrAssignmentListCreateAPIView(APIView):
    permission_classes = [IsVerifiedOwner]

    def get(self, request):
        assignments = TenantQrAssignment.objects.filter(
            owner=request.user,
            qr_config__owner=request.user,
        ).select_related("qr_config")

        tenant_id = request.query_params.get("tenant_id")
        if tenant_id:
            assignments = assignments.filter(
                tenant_id=tenant_id
            )

        serializer = TenantQrAssignmentSerializer(
            assignments,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)

    def post(self, request):
        tenant_id = request.data.get("tenant_id")

        if not tenant_id:
            return Response(
                {"tenant_id": "This field is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            tenant_id = int(tenant_id)
        except (TypeError, ValueError):
            return Response(
                {"tenant_id": "Enter a valid tenant ID."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify that this tenant has an agreement associated
        # with a property owned by the authenticated owner.
        tenant_is_owned = RentalAgreement.objects.filter(
            tenant_id=tenant_id,
            room__property__owner=request.user,
        ).exists()

        if not tenant_is_owned:
            return Response(
                {
                    "tenant_id": (
                        "This tenant is not associated with "
                        "a property owned by you."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = TenantQrAssignmentSerializer(
            data=request.data,
            context={"request": request},
        )

        serializer.is_valid(raise_exception=True)

        # One QR assignment per owner and tenant.
        assignment, created = (
            TenantQrAssignment.objects.update_or_create(
                owner=request.user,
                tenant_id=tenant_id,
                defaults={
                    "qr_config": serializer.validated_data["qr_config"],
                },
            )
        )

        response_serializer = TenantQrAssignmentSerializer(
            assignment,
            context={"request": request},
        )

        return Response(
            response_serializer.data,
            status=(
                status.HTTP_201_CREATED
                if created
                else status.HTTP_200_OK
            ),
        )


class TenantQrAssignmentDetailAPIView(
    generics.RetrieveUpdateDestroyAPIView
):
    serializer_class = TenantQrAssignmentSerializer
    permission_classes = [IsVerifiedOwner]

    def get_queryset(self):
        return TenantQrAssignment.objects.filter(
            owner=self.request.user,
            qr_config__owner=self.request.user,
        )

    def perform_update(self, serializer):
        tenant_id = serializer.validated_data.get(
            "tenant_id",
            serializer.instance.tenant_id,
        )

        tenant_is_owned = RentalAgreement.objects.filter(
            tenant_id=tenant_id,
            room__property__owner=self.request.user,
        ).exists()

        if not tenant_is_owned:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied(
                "This tenant is not associated with a property you own."
            )

        serializer.save(owner=self.request.user)
