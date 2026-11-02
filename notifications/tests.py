
from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from properties.models import Property, Room
from tenants.models import Tenant, RentalAgreement
from billing.models import RentRecord
from electricity.models import ElectricityMeter, MeterReading, ElectricityBill
from notifications.models import Notification
from notifications.services import generate_notifications



User = get_user_model()

class NotificationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test_owner", email="test-owner@example.com",
            password="StrongTestPassword!2026",
        )
        self.client = APIClient()
        self.today = timezone.localdate()
        self.client.force_authenticate(user=self.user)

        self.property = Property.objects.create(
            owner=self.user,
            name="Test Hostel",
            property_type="HOSTEL",
            address="Test Address",
            city="Indore",
            state="Madhya Pradesh",
            pin_code="452001",
            monthly_rent=Decimal("5000.00"),
            security_deposit=Decimal("5000.00"),
            rent_due_day=5,
            electricity_rate=Decimal("8.00"),
        )

        self.room = Room.objects.create(
            property=self.property,
            room_number="101",
            floor=1,
            room_type="SINGLE",
            monthly_rent=Decimal("5000.00"),
            security_deposit=Decimal("5000.00"),
            status="VACANT",
        )

        self.tenant = Tenant.objects.create(
            owner=self.user,
            full_name="Test Tenant",
            email="tenant@example.com",
            phone="9876543210",
        )

        self.agreement = RentalAgreement.objects.create(
            tenant=self.tenant,
            room=self.room,
            start_date=self.today - timedelta(days=30),
            monthly_rent=Decimal("5000.00"),
            security_deposit=Decimal("5000.00"),
            status="ACTIVE",
        )

    def create_rent(self, due_date, amount="5000.00", paid="0.00"):
        return RentRecord.objects.create(
            agreement=self.agreement,
            billing_month=self.today.replace(day=1),
            rent_amount=Decimal(amount),
            due_date=due_date,
            amount_paid=Decimal(paid),
            status="PENDING",
        )

    def test_upcoming_rent_notification(self):
        self.create_rent(self.today + timedelta(days=2))

        result = generate_notifications(days_ahead=3, as_of=self.today)

        self.assertEqual(result["created_count"], 1)
        self.assertTrue(
            Notification.objects.filter(
                notification_type="RENT_UPCOMING"
            ).exists()
        )

    def test_overdue_rent_notification(self):
        self.create_rent(self.today - timedelta(days=2))

        generate_notifications(days_ahead=3, as_of=self.today)

        self.assertTrue(
            Notification.objects.filter(
                notification_type="RENT_OVERDUE"
            ).exists()
        )

    def test_duplicate_notification_is_not_created(self):
        self.create_rent(self.today + timedelta(days=1))

        first = generate_notifications(3, self.today)
        second = generate_notifications(3, self.today)

        self.assertEqual(first["created_count"], 1)
        self.assertEqual(second["created_count"], 0)
        self.assertEqual(Notification.objects.count(), 1)

    def test_fully_paid_rent_is_ignored(self):
        self.create_rent(
            self.today - timedelta(days=2),
            amount="5000.00",
            paid="5000.00",
        )

        generate_notifications(3, self.today)

        self.assertEqual(Notification.objects.count(), 0)

    def test_electricity_bill_notification(self):
        meter = ElectricityMeter.objects.create(
            room=self.room,
            meter_number="METER-101",
            installation_date=self.today - timedelta(days=30),
        )

        reading = MeterReading.objects.create(
            meter=meter,
            reading_date=self.today - timedelta(days=1),
            previous_reading=Decimal("100.00"),
            current_reading=Decimal("150.00"),
        )

        ElectricityBill.objects.create(
            meter=meter,
            reading=reading,
            billing_month=self.today.replace(day=1),
            units_consumed=Decimal("50.00"),
            rate_per_unit=Decimal("8.00"),
            total_amount=Decimal("400.00"),
            due_date=self.today + timedelta(days=2),
            amount_paid=Decimal("0.00"),
            status="PENDING",
        )

        generate_notifications(3, self.today)

        self.assertTrue(
            Notification.objects.filter(
                notification_type="ELECTRICITY_UPCOMING",
                tenant=self.tenant,
            ).exists()
        )

    def test_notification_can_be_marked_read(self):
        self.create_rent(self.today + timedelta(days=1))
        generate_notifications(3, self.today)

        notification = Notification.objects.get()

        response = self.client.patch(
            f"/api/notifications/{notification.pk}/",
            {"is_read": True},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        notification.refresh_from_db()
        self.assertTrue(notification.is_read)
        self.assertIsNotNone(notification.read_at)

    def test_notification_can_be_marked_unread(self):
        self.create_rent(self.today + timedelta(days=1))
        generate_notifications(3, self.today)

        notification = Notification.objects.get()
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()

        response = self.client.patch(
            f"/api/notifications/{notification.pk}/",
            {"is_read": False},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        notification.refresh_from_db()
        self.assertFalse(notification.is_read)
        self.assertIsNone(notification.read_at)

    def test_invalid_days_ahead_is_rejected(self):
        response = self.client.post(
            "/api/notifications/generate/",
            {"days_ahead": "abc"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_unread_count(self):
        self.create_rent(self.today + timedelta(days=1))
        generate_notifications(3, self.today)

        response = self.client.get(
            "/api/notifications/unread-count/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["unread_count"], 1)

    def test_pending_bills_endpoint(self):
        self.create_rent(self.today + timedelta(days=2))

        response = self.client.get("/api/notifications/pending-bills/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            response.data["results"][0]["bill_type"],
            "RENT",
        )

    def test_invalid_reminder_window_is_rejected(self):
        with self.assertRaises(ValueError):
            generate_notifications(days_ahead=400, as_of=self.today)

    def test_send_notification_message_and_whatsapp_link(self):
        self.create_rent(self.today + timedelta(days=1))
        generate_notifications(3, self.today)
        notif = Notification.objects.first()

        # Test WhatsApp link generation
        link_res = self.client.get(f"/api/notifications/{notif.pk}/whatsapp-link/")
        self.assertEqual(link_res.status_code, 200)
        self.assertIn("whatsapp_url", link_res.data)
        self.assertIn("wa.me/919876543210", link_res.data["whatsapp_url"])

        # Test sending message
        send_res = self.client.post(
            f"/api/notifications/{notif.pk}/send/",
            {"channel": "WHATSAPP"},
            format="json",
        )
        self.assertEqual(send_res.status_code, 200)
        notif.refresh_from_db()
        self.assertTrue(notif.is_sent)
        self.assertEqual(notif.sent_via, "WHATSAPP")
        self.assertEqual(notif.delivery_status, "SENT")

        # Test bulk send
        bulk_res = self.client.post(
            "/api/notifications/send-bulk/",
            {"channel": "WHATSAPP"},
            format="json",
        )
        self.assertEqual(bulk_res.status_code, 200)
        self.assertIn("total_processed", bulk_res.data)

        # Test bulk send with BOTH channels and tenant_ids
        both_res = self.client.post(
            "/api/notifications/send-bulk/",
            {"channel": "BOTH", "tenant_ids": [self.tenant.id]},
            format="json",
        )
        self.assertEqual(both_res.status_code, 200)
        self.assertIn("total_processed", both_res.data)
        self.assertTrue(both_res.data["dispatched"][0]["whatsapp_sent"])
        self.assertTrue(both_res.data["dispatched"][0]["email_sent"])
