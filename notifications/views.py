
from decimal import Decimal

from django.utils import timezone
from django.utils.dateparse import parse_date

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from billing.models import RentRecord
from electricity.models import ElectricityBill
from tenants.models import RentalAgreement

from .models import Notification
from .serializers import NotificationSerializer
from .services import generate_notifications, get_outstanding_amount


class NotificationListAPIView(generics.ListAPIView):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        queryset = Notification.objects.select_related("tenant").filter(
            tenant__owner=self.request.user
        )

        tenant_id = self.request.query_params.get("tenant_id")
        is_read = self.request.query_params.get("is_read")
        notification_type = self.request.query_params.get(
            "notification_type"
        )

        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)

        if is_read is not None:
            if is_read.lower() in ["true", "1"]:
                queryset = queryset.filter(is_read=True)
            elif is_read.lower() in ["false", "0"]:
                queryset = queryset.filter(is_read=False)

        if notification_type:
            queryset = queryset.filter(
                notification_type=notification_type
            )

        return queryset


class NotificationDetailAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = NotificationSerializer
    http_method_names = ["get", "patch", "head", "options"]

    def get_queryset(self):
        return Notification.objects.select_related("tenant").filter(
            tenant__owner=self.request.user
        )


class UnreadNotificationCountAPIView(APIView):
    def get(self, request):
        tenant_id = request.query_params.get("tenant_id")

        queryset = Notification.objects.filter(
            is_read=False, tenant__owner=request.user
        )

        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)

        return Response({"unread_count": queryset.count()})


class GenerateNotificationsAPIView(APIView):
    def post(self, request):
        raw_days = request.data.get("days_ahead", 3)

        try:
            if isinstance(raw_days, bool):
                raise ValueError
            if isinstance(raw_days, float) and not raw_days.is_integer():
                raise ValueError
            days_ahead = int(raw_days)
        except (TypeError, ValueError):
            return Response(
                {"error": "days_ahead integer hona chahiye."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        as_of = timezone.localdate()
        raw_date = request.data.get("as_of")

        if raw_date:
            as_of = parse_date(str(raw_date))
            if as_of is None:
                return Response(
                    {"error": "as_of date YYYY-MM-DD format mein dein."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        try:
            result = generate_notifications(
                days_ahead=days_ahead,
                as_of=as_of,
                owner=request.user,
            )
        except ValueError as error:
            return Response(
                {"error": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "message": "Notification generation complete.",
                "created_count": result["created_count"],
                "days_ahead": result["days_ahead"],
                "as_of": result["as_of"].isoformat(),
            },
            status=status.HTTP_200_OK,
        )


class PendingBillsAPIView(APIView):
    def get(self, request):
        today = timezone.localdate()
        tenant_id = request.query_params.get("tenant_id")
        results = []

        rent_records = RentRecord.objects.select_related(
            "agreement__tenant", "agreement__room__property"
        ).filter(
            agreement__room__property__owner=request.user,
            agreement__tenant__owner=request.user,
        )

        if tenant_id:
            rent_records = rent_records.filter(
                agreement__tenant_id=tenant_id
            )

        for record in rent_records:
            remaining = get_outstanding_amount(
                record.rent_amount,
                record.amount_paid,
            )

            if remaining <= 0:
                continue

            results.append({
                "bill_type": "RENT",
                "bill_id": record.pk,
                "tenant_id": record.agreement.tenant_id,
                "tenant_name": record.agreement.tenant.full_name,
                "due_date": record.due_date.isoformat(),
                "total_amount": str(record.rent_amount),
                "amount_paid": str(record.amount_paid),
                "amount_due": str(remaining),
                "status": (
                    "OVERDUE"
                    if record.due_date < today
                    else record.status
                ),
            })

        electricity_bills = ElectricityBill.objects.select_related(
            "meter", "meter__room", "meter__room__property"
        ).filter(meter__room__property__owner=request.user)

        for bill in electricity_bills:
            remaining = get_outstanding_amount(
                bill.total_amount,
                bill.amount_paid,
            )

            if remaining <= 0:
                continue

            agreement = (
                RentalAgreement.objects.select_related("tenant")
                .filter(
                    room_id=bill.meter.room_id,
                    status="ACTIVE",
                    room__property__owner=request.user,
                    tenant__owner=request.user,
                )
                .order_by("-start_date", "-pk")
                .first()
            )

            if agreement is None:
                continue

            if tenant_id and str(agreement.tenant_id) != str(tenant_id):
                continue

            results.append({
                "bill_type": "ELECTRICITY",
                "bill_id": bill.pk,
                "tenant_id": agreement.tenant_id,
                "tenant_name": agreement.tenant.full_name,
                "due_date": bill.due_date.isoformat(),
                "total_amount": str(bill.total_amount),
                "amount_paid": str(bill.amount_paid),
                "amount_due": str(remaining),
                "status": (
                    "OVERDUE"
                    if bill.due_date < today
                    else bill.status
                ),
            })

        results.sort(key=lambda item: item["due_date"])

        return Response({
            "count": len(results),
            "results": results,
        })


from .message_service import (
    send_actual_notification,
    generate_whatsapp_url,
    format_notification_text,
)


class SendNotificationMessageAPIView(APIView):
    def post(self, request, pk):
        try:
            notification = Notification.objects.select_related(
                "tenant", "tenant__owner", "rent_record__agreement", "electricity_bill__meter__room"
            ).get(
                pk=pk,
                tenant__owner=request.user,
            )
        except Notification.DoesNotExist:
            return Response(
                {"error": "Notification nahi mili."},
                status=status.HTTP_404_NOT_FOUND,
            )

        channel = request.data.get("channel", "WHATSAPP")
        try:
            result = send_actual_notification(notification, channel=channel)
            serializer = NotificationSerializer(notification)
            return Response(
                {
                    "message": result["message"],
                    "delivery": result,
                    "notification": serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as error:
            return Response(
                {"error": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class SendBulkNotificationMessagesAPIView(APIView):
    def post(self, request):
        channel = request.data.get("channel", "WHATSAPP")
        channels = request.data.get("channels", [])
        if "WHATSAPP" in channels and "EMAIL" in channels:
            channel = "BOTH"
        elif channels and not request.data.get("channel"):
            channel = channels[0]

        tenant_ids = request.data.get("tenant_ids") or []
        tenant_id = request.data.get("tenant_id")
        if tenant_id and tenant_id not in tenant_ids:
            tenant_ids.append(tenant_id)

        rent_record_ids = request.data.get("rent_record_ids") or []

        # Ensure notification exists for selected rent records
        if rent_record_ids:
            from billing.models import RentRecord
            records = RentRecord.objects.select_related("agreement__tenant").filter(
                id__in=rent_record_ids,
                agreement__room__property__owner=request.user,
            )
            for rec in records:
                notif = Notification.objects.filter(
                    rent_record=rec,
                    tenant=rec.agreement.tenant,
                ).first()
                if not notif:
                    due = rec.rent_amount - (rec.amount_paid or 0)
                    Notification.objects.create(
                        tenant=rec.agreement.tenant,
                        rent_record=rec,
                        notification_type="RENT_UPCOMING" if rec.due_date >= timezone.localdate() else "RENT_OVERDUE",
                        title=f"Monthly Rent Bill ({rec.billing_month.strftime('%b %Y')})",
                        message=f"Rent bill for Room {rec.agreement.room.room_number}: Rs. {due}",
                        due_date=rec.due_date,
                        amount_due=due,
                    )

        # Ensure notification exists for selected tenants
        if tenant_ids:
            from tenants.models import Tenant
            tenants = Tenant.objects.filter(id__in=tenant_ids, owner=request.user)
            for t in tenants:
                existing = Notification.objects.filter(tenant=t, is_read=False).first()
                if not existing:
                    active_ag = t.agreements.filter(status="ACTIVE").first()
                    latest_rent_id = t.agreements.filter(status="ACTIVE").values_list("rent_records__id", flat=True).first()
                    rec = None
                    if latest_rent_id:
                        from billing.models import RentRecord
                        rec = RentRecord.objects.filter(id=latest_rent_id).first()
                    due = rec.rent_amount - (rec.amount_paid or 0) if rec else (active_ag.monthly_rent if active_ag else Decimal("0.00"))
                    Notification.objects.create(
                        tenant=t,
                        rent_record=rec,
                        notification_type="RENT_UPCOMING",
                        title="Monthly Rent Bill",
                        message=f"Pending dues for tenant {t.full_name}: Rs. {due}",
                        due_date=rec.due_date if rec else timezone.localdate(),
                        amount_due=due,
                    )

        queryset = Notification.objects.select_related(
            "tenant", "tenant__owner", "rent_record__agreement", "electricity_bill__meter__room"
        ).filter(
            tenant__owner=request.user,
        )

        if tenant_ids:
            queryset = queryset.filter(tenant_id__in=tenant_ids)
        elif rent_record_ids:
            queryset = queryset.filter(rent_record_id__in=rent_record_ids)

        only_unsent = request.data.get("only_unsent", False)
        if only_unsent:
            queryset = queryset.filter(is_sent=False)

        dispatched = []
        errors = []

        processed_tenants = set()
        for notif in queryset.order_by("-id")[:100]:
            if notif.tenant_id in processed_tenants and len(tenant_ids) > 0:
                continue
            processed_tenants.add(notif.tenant_id)
            try:
                res = send_actual_notification(notif, channel=channel)
                dispatched.append({
                    "notification_id": notif.pk,
                    "tenant_id": notif.tenant.pk,
                    "tenant_name": notif.tenant.full_name,
                    "tenant_phone": notif.tenant.phone,
                    "tenant_email": notif.tenant.email,
                    "amount_due": str(notif.amount_due),
                    "due_date": str(notif.due_date),
                    "channel": channel,
                    "whatsapp_url": res.get("whatsapp_url", ""),
                    "email_sent": res.get("email_sent", channel in ["EMAIL", "BOTH", "ALL"]),
                    "whatsapp_sent": res.get("whatsapp_sent", channel in ["WHATSAPP", "BOTH", "ALL"]),
                    "message": res["message"],
                })
            except Exception as e:
                errors.append({
                    "notification_id": notif.pk,
                    "tenant_id": notif.tenant.pk,
                    "tenant_name": notif.tenant.full_name,
                    "error": str(e),
                })

        return Response(
            {
                "message": f"{len(dispatched)} bills processed.",
                "total_processed": len(dispatched),
                "channel": channel,
                "dispatched": dispatched,
                "errors": errors,
            },
            status=status.HTTP_200_OK,
        )


class NotificationWhatsAppLinkAPIView(APIView):
    def get(self, request, pk):
        try:
            notification = Notification.objects.select_related(
                "tenant", "tenant__owner", "rent_record__agreement", "electricity_bill__meter__room"
            ).get(
                pk=pk,
                tenant__owner=request.user,
            )
        except Notification.DoesNotExist:
            return Response(
                {"error": "Notification nahi mili."},
                status=status.HTTP_404_NOT_FOUND,
            )

        url = generate_whatsapp_url(notification)
        text = format_notification_text(notification)
        return Response({
            "whatsapp_url": url,
            "message_text": text,
            "recipient_phone": notification.tenant.phone,
        })
