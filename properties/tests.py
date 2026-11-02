from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from properties.models import Property, Room
from tenants.models import Tenant, RentalAgreement
from billing.models import RentRecord
from electricity.models import ElectricityMeter, MeterReading, ElectricityBill
from payments.models import Payment
from notifications.models import Notification

User = get_user_model()


class OwnerIsolationAPITests(APITestCase):
    """Regression tests for cross-owner reads and relationship writes."""

    def setUp(self):
        self.owner_a = User.objects.create_user(
            username="owner_a", email="a@example.com", password="StrongTestPassword!2026"
        )
        self.owner_b = User.objects.create_user(
            username="owner_b", email="b@example.com", password="StrongTestPassword!2026"
        )
        today = timezone.localdate()
        month = today.replace(day=1)

        self.property_a = self.make_property(self.owner_a, "Owner A Property")
        self.property_b = self.make_property(self.owner_b, "Owner B Property")
        self.room_a = self.make_room(self.property_a, "A-101")
        self.room_b = self.make_room(self.property_b, "B-101")
        self.tenant_a = Tenant.objects.create(
            owner=self.owner_a, full_name="Tenant A", phone="9000000001"
        )
        self.tenant_b = Tenant.objects.create(
            owner=self.owner_b, full_name="Tenant B", phone="9000000002"
        )
        self.agreement_a = self.make_agreement(self.tenant_a, self.room_a, today)
        self.agreement_b = self.make_agreement(self.tenant_b, self.room_b, today)
        self.rent_a = self.make_rent(self.agreement_a, month, today)
        self.rent_b = self.make_rent(self.agreement_b, month, today)
        self.meter_a, self.reading_a, self.bill_a = self.make_electricity(self.room_a, "M-A", today, month)
        self.meter_b, self.reading_b, self.bill_b = self.make_electricity(self.room_b, "M-B", today, month)
        self.payment_a = self.make_payment(self.agreement_a, self.rent_a)
        self.payment_b = self.make_payment(self.agreement_b, self.rent_b)
        self.notification_a = self.make_notification(self.tenant_a, self.rent_a, today)
        self.notification_b = self.make_notification(self.tenant_b, self.rent_b, today)
        self.client.force_authenticate(user=self.owner_a)

    @staticmethod
    def make_property(owner, name):
        return Property.objects.create(
            owner=owner,
            name=name,
            property_type="BUILDING",
            address="Test Road",
            city="Indore",
            state="Madhya Pradesh",
            pin_code="452001",
            monthly_rent=Decimal("5000.00"),
            security_deposit=Decimal("5000.00"),
            rent_due_day=5,
            electricity_rate=Decimal("8.00"),
        )

    @staticmethod
    def make_room(prop, number):
        return Room.objects.create(
            property=prop,
            room_number=number,
            floor="1",
            room_type="SINGLE",
            monthly_rent=Decimal("5000.00"),
            security_deposit=Decimal("5000.00"),
            status="OCCUPIED",
        )

    @staticmethod
    def make_agreement(tenant, room, today):
        return RentalAgreement.objects.create(
            tenant=tenant,
            room=room,
            start_date=today,
            monthly_rent=Decimal("5000.00"),
            security_deposit=Decimal("5000.00"),
            status="ACTIVE",
        )

    @staticmethod
    def make_rent(agreement, month, today):
        return RentRecord.objects.create(
            agreement=agreement,
            billing_month=month,
            rent_amount=Decimal("5000.00"),
            due_date=today,
            amount_paid=Decimal("0.00"),
            status="PENDING",
        )

    @staticmethod
    def make_electricity(room, number, today, month):
        meter = ElectricityMeter.objects.create(
            room=room, meter_number=number, installation_date=today, is_active=True
        )
        reading = MeterReading.objects.create(
            meter=meter,
            reading_date=today,
            previous_reading=Decimal("100.00"),
            current_reading=Decimal("150.00"),
        )
        bill = ElectricityBill.objects.create(
            meter=meter,
            reading=reading,
            billing_month=month,
            units_consumed=Decimal("50.00"),
            rate_per_unit=Decimal("8.00"),
            total_amount=Decimal("400.00"),
            due_date=today,
            amount_paid=Decimal("0.00"),
            status="PENDING",
        )
        return meter, reading, bill

    @staticmethod
    def make_payment(agreement, rent):
        return Payment.objects.create(
            agreement=agreement,
            rent_record=rent,
            amount=Decimal("250.00"),
            payment_date=timezone.now(),
            payment_method="UPI",
            status="COMPLETED",
        )

    @staticmethod
    def make_notification(tenant, rent, today):
        return Notification.objects.create(
            tenant=tenant,
            rent_record=rent,
            notification_type="RENT_UPCOMING",
            title="Rent due soon",
            message="Test reminder",
            due_date=today,
            amount_due=Decimal("5000.00"),
        )

    def test_all_collection_endpoints_only_return_current_owners_data(self):
        endpoint_and_expected_id = [
            ("/api/properties/", self.property_a.pk),
            ("/api/properties/rooms/", self.room_a.pk),
            ("/api/tenants/", self.tenant_a.pk),
            ("/api/tenants/rental-agreements/", self.agreement_a.pk),
            ("/api/billing/", self.rent_a.pk),
            ("/api/electricity/meters/", self.meter_a.pk),
            ("/api/electricity/readings/", self.reading_a.pk),
            ("/api/electricity/bills/", self.bill_a.pk),
            ("/api/payments/", self.payment_a.pk),
            ("/api/notifications/", self.notification_a.pk),
        ]
        for endpoint, expected_id in endpoint_and_expected_id:
            with self.subTest(endpoint=endpoint):
                response = self.client.get(endpoint)
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual([row["id"] for row in response.data], [expected_id])

    def test_other_owners_details_return_not_found(self):
        other_owner_detail_urls = [
            f"/api/properties/{self.property_b.pk}/",
            f"/api/properties/rooms/{self.room_b.pk}/",
            f"/api/tenants/{self.tenant_b.pk}/",
            f"/api/tenants/rental-agreements/{self.agreement_b.pk}/",
            f"/api/billing/{self.rent_b.pk}/",
            f"/api/electricity/meters/{self.meter_b.pk}/",
            f"/api/electricity/readings/{self.reading_b.pk}/",
            f"/api/electricity/bills/{self.bill_b.pk}/",
            f"/api/payments/{self.payment_b.pk}/",
            f"/api/notifications/{self.notification_b.pk}/",
        ]
        for endpoint in other_owner_detail_urls:
            with self.subTest(endpoint=endpoint):
                response = self.client.get(endpoint)
                self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_room_cannot_be_created_under_another_owners_property(self):
        response = self.client.post(
            "/api/properties/rooms/",
            {
                "property": self.property_b.pk,
                "room_number": "A-999",
                "floor": "1",
                "room_type": "SINGLE",
                "monthly_rent": "5000.00",
                "security_deposit": "5000.00",
                "status": "VACANT",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Room.objects.filter(room_number="A-999").exists())

    def test_agreement_cannot_link_tenant_and_room_from_different_owners(self):
        response = self.client.post(
            "/api/tenants/rental-agreements/",
            {
                "tenant": self.tenant_a.pk,
                "room": self.room_b.pk,
                "start_date": timezone.localdate().isoformat(),
                "monthly_rent": "5000.00",
                "security_deposit": "5000.00",
                "status": "ACTIVE",
                "notes": "",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(
            RentalAgreement.objects.filter(tenant=self.tenant_a, room=self.room_b).exists()
        )

    def test_dashboard_and_notification_counts_are_owner_scoped(self):
        dashboard = self.client.get("/api/dashboard/")
        self.assertEqual(dashboard.status_code, status.HTTP_200_OK)
        self.assertEqual(dashboard.data["rooms"]["total"], 1)
        self.assertEqual(dashboard.data["tenants"]["active_agreements"], 1)

        unread = self.client.get("/api/notifications/unread-count/")
        self.assertEqual(unread.status_code, status.HTTP_200_OK)
        self.assertEqual(unread.data["unread_count"], 1)

    def test_property_create_assigns_logged_in_owner(self):
        response = self.client.post(
            "/api/properties/",
            {
                "name": "Owner A New Property",
                "property_type": "BUILDING",
                "address": "New Road",
                "city": "Indore",
                "state": "Madhya Pradesh",
                "pin_code": "452001",
                "monthly_rent": "0.00",
                "security_deposit": "0.00",
                "rent_due_day": 5,
                "electricity_rate": "8.00",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data["owner"], self.owner_a.pk)
    def test_rent_record_cannot_be_created_for_another_owners_agreement(self):
        response = self.client.post(
            "/api/billing/",
            {
                "agreement": self.agreement_b.pk,
                "billing_month": timezone.localdate().replace(day=1).isoformat(),
                "rent_amount": "5000.00",
                "due_date": timezone.localdate().isoformat(),
                "notes": "",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_meter_cannot_be_created_for_another_owners_room(self):
        response = self.client.post(
            "/api/electricity/meters/",
            {
                "room": self.room_b.pk,
                "meter_number": "TRY-OTHER-OWNER",
                "installation_date": timezone.localdate().isoformat(),
                "is_active": True,
                "notes": "",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_other_owners_reading_cannot_generate_an_electricity_bill(self):
        response = self.client.post(
            "/api/electricity/bills/generate/",
            {"reading_id": self.reading_b.pk},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_payment_cannot_reference_another_owners_rent_record(self):
        response = self.client.post(
            "/api/payments/",
            {
                "agreement": self.agreement_a.pk,
                "rent_record": self.rent_b.pk,
                "electricity_bill": None,
                "amount": "100.00",
                "payment_date": timezone.now().isoformat(),
                "payment_method": "UPI",
                "status": "COMPLETED",
                "transaction_reference": "",
                "notes": "",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Payment.objects.filter(rent_record=self.rent_b, amount=Decimal("100.00")).exists())

