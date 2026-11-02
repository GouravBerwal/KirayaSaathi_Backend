from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from billing.models import RentRecord
from payments.models import Payment
from properties.models import Property, Room
from tenants.models import RentalAgreement, Tenant

User = get_user_model()


class ReportsAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="report_user",
            email="report_user@example.com",
            password="StrongPassword!2026",
        )
        self.client.force_authenticate(user=self.user)

        self.property = Property.objects.create(
            owner=self.user,
            name="Green Villa",
            property_type="HOSTEL",
            address="123 Street",
            city="Indore",
            state="Madhya Pradesh",
            pin_code="452001",
            monthly_rent=8000,
            security_deposit=8000,
            rent_due_day=5,
            electricity_rate=8,
        )

        self.room1 = Room.objects.create(
            property=self.property,
            room_number="101",
            floor=1,
            monthly_rent=8000,
            status="OCCUPIED",
        )

        self.room2 = Room.objects.create(
            property=self.property,
            room_number="102",
            floor=1,
            monthly_rent=8000,
            status="VACANT",
        )

        self.tenant = Tenant.objects.create(
            owner=self.user,
            full_name="Rohan Verma",
            phone="9876543210",
            email="rohan@example.com",
        )

        today = date.today()
        self.agreement = RentalAgreement.objects.create(
            tenant=self.tenant,
            room=self.room1,
            start_date=today,
            monthly_rent=8000,
            security_deposit=8000,
            status="ACTIVE",
        )

        # Rent record for this month
        self.rent_record = RentRecord.objects.create(
            agreement=self.agreement,
            billing_month=date(today.year, today.month, 1),
            rent_amount=Decimal("8000.00"),
            amount_paid=Decimal("5000.00"),
            due_date=date(today.year, today.month, 5),
            status="PARTIAL",
        )

        # Payment for this rent record
        self.payment = Payment.objects.create(
            agreement=self.agreement,
            rent_record=self.rent_record,
            amount=Decimal("5000.00"),
            payment_date=timezone.now(),
            payment_method="UPI",
            status="COMPLETED",
        )

    def test_reports_endpoint_returns_accurate_summary_and_income(self):
        response = self.client.get("/api/reports/")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        summary = data.get("summary", {})

        # Rent collected should be at least 5000.00
        self.assertEqual(float(summary.get("rent_collected", 0)), 5000.00)

        # Outstanding rent should be 3000.00 (8000 - 5000)
        self.assertEqual(float(summary.get("outstanding_rent", 0)), 3000.00)

        # Total rooms: 2, Occupied: 1, Occupancy rate: 50.0%
        self.assertEqual(summary.get("total_rooms"), 2)
        self.assertEqual(summary.get("occupied_rooms"), 1)
        self.assertEqual(float(summary.get("occupancy_rate", 0)), 50.0)

        # Monthly income check
        monthly_income = data.get("monthly_income", [])
        self.assertGreater(len(monthly_income), 0)

        # Property performance check
        property_perf = data.get("property_performance", [])
        self.assertEqual(len(property_perf), 1)
        self.assertEqual(property_perf[0]["property_name"], "Green Villa")
        self.assertEqual(float(property_perf[0]["collected_rent"]), 5000.00)
        self.assertEqual(float(property_perf[0]["pending_rent"]), 3000.00)
