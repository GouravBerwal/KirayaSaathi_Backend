
from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model

from properties.models import Property, Room
from tenants.models import Tenant, RentalAgreement
from billing.models import RentRecord
from billing.services import (
    calculate_due_date,
    generate_monthly_rent_records,
)



User = get_user_model()

class RentGenerationTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="test_owner", email="test-owner@example.com",
            password="StrongTestPassword!2026",
        )
        # Property create karna
        self.property = Property.objects.create(
            owner=self.user,
            name="Test Property",
            property_type="BUILDING",
            address="Test Address",
            city="Indore",
            state="Madhya Pradesh",
            pin_code="452001",
            monthly_rent=Decimal("10000.00"),
            security_deposit=Decimal("5000.00"),
            rent_due_day=5,
            electricity_rate=Decimal("8.00"),
        )

        # Room create karna
        self.room = Room.objects.create(
            property=self.property,
            room_number="T101",
            floor=1,
            room_type="SINGLE",
            monthly_rent=Decimal("10000.00"),
            security_deposit=Decimal("5000.00"),
            status="VACANT",
        )

        # Tenant create karna
        self.tenant = Tenant.objects.create(
            owner=self.user,
            full_name="Test Tenant",
            email="tenant@example.com",
            phone="9876543210",
        )

        # Rental agreement create karna
        self.agreement = RentalAgreement.objects.create(
            tenant=self.tenant,
            room=self.room,
            start_date=date(2026, 10, 1),
            monthly_rent=Decimal("10000.00"),
            security_deposit=Decimal("5000.00"),
            status="ACTIVE",
        )

    def test_rent_record_is_created(self):
        result = generate_monthly_rent_records(
            as_of=date(2026, 10, 22)
        )

        self.assertEqual(result["created"], 1)

        record = RentRecord.objects.get(
            agreement=self.agreement,
            billing_month=date(2026, 10, 1),
        )

        self.assertEqual(
            record.rent_amount,
            Decimal("10000.00"),
        )
        self.assertEqual(record.due_date, date(2026, 10, 5))
        self.assertEqual(record.status, "OVERDUE")

    def test_running_generation_twice_does_not_duplicate(self):
        first_result = generate_monthly_rent_records(
            as_of=date(2026, 10, 22)
        )

        second_result = generate_monthly_rent_records(
            as_of=date(2026, 10, 22)
        )

        self.assertEqual(first_result["created"], 1)
        self.assertEqual(second_result["created"], 0)
        self.assertEqual(second_result["already_existing"], 1)

        self.assertEqual(
            RentRecord.objects.filter(
                agreement=self.agreement,
                billing_month=date(2026, 10, 1),
            ).count(),
            1,
        )

    def test_future_agreement_does_not_generate_rent(self):
        self.agreement.start_date = date(2026, 11, 1)
        self.agreement.save(update_fields=["start_date"])

        result = generate_monthly_rent_records(
            as_of=date(2026, 10, 22)
        )

        self.assertEqual(result["created"], 0)
        self.assertEqual(RentRecord.objects.count(), 0)

    def test_due_date_stays_within_month(self):
        due_date = calculate_due_date(
            date(2026, 2, 1),
            31,
        )

        self.assertEqual(due_date, date(2026, 2, 28))

    def test_future_due_date_has_pending_status(self):
        result = generate_monthly_rent_records(
            as_of=date(2026, 10, 1)
        )

        self.assertEqual(result["created"], 1)

        record = RentRecord.objects.get(
            agreement=self.agreement,
            billing_month=date(2026, 10, 1),
        )

        self.assertEqual(record.status, "PENDING")

    def test_existing_rent_record_is_not_overwritten(self):
        RentRecord.objects.create(
            agreement=self.agreement,
            billing_month=date(2026, 10, 1),
            rent_amount=Decimal("12000.00"),
            due_date=date(2026, 10, 10),
            amount_paid=Decimal("12000.00"),
            status="PAID",
        )

        result = generate_monthly_rent_records(
            as_of=date(2026, 10, 22)
        )

        record = RentRecord.objects.get(
            agreement=self.agreement,
            billing_month=date(2026, 10, 1),
        )

        self.assertEqual(result["created"], 0)
        self.assertEqual(result["already_existing"], 1)
        self.assertEqual(
            record.rent_amount,
            Decimal("12000.00"),
        )
        self.assertEqual(record.status, "PAID")
        self.assertEqual(
            record.amount_paid,
            Decimal("12000.00"),
        )


class ArchiveAndRolloverTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="archive_owner",
            email="archive-owner@example.com",
            password="StrongTestPassword!2026",
        )
        self.property = Property.objects.create(
            owner=self.user,
            name="Green Valley",
            property_type="BUILDING",
            address="Scheme 78",
            city="Indore",
            state="MP",
            pin_code="452010",
            monthly_rent=Decimal("8000.00"),
            rent_due_day=5,
            electricity_rate=Decimal("10.00"),
        )
        self.room = Room.objects.create(
            property=self.property,
            room_number="101",
            floor="1",
            monthly_rent=Decimal("8000.00"),
            status="OCCUPIED",
        )
        self.tenant = Tenant.objects.create(
            owner=self.user,
            full_name="Rahul Sharma",
            phone="9826012345",
        )
        self.agreement = RentalAgreement.objects.create(
            tenant=self.tenant,
            room=self.room,
            start_date=date(2026, 10, 1),
            monthly_rent=Decimal("8000.00"),
            status="ACTIVE",
        )
        self.meter = from_elec_models = None
        from electricity.models import ElectricityMeter, MeterReading, ElectricityBill
        self.meter = ElectricityMeter.objects.create(
            room=self.room,
            meter_number="MTR-101",
            installation_date=date(2026, 10, 1),
            is_active=True,
        )
        self.reading_oct = MeterReading.objects.create(
            meter=self.meter,
            reading_date=date(2026, 10, 20),
            previous_reading=Decimal("100.00"),
            current_reading=Decimal("150.00"),
        )
        self.bill_oct = ElectricityBill.objects.create(
            meter=self.meter,
            reading=self.reading_oct,
            billing_month=date(2026, 10, 1),
            units_consumed=Decimal("50.00"),
            rate_per_unit=Decimal("10.00"),
            total_amount=Decimal("500.00"),
            due_date=date(2026, 10, 5),
            amount_paid=Decimal("500.00"),
            status="PAID",
        )
        self.rent_oct = RentRecord.objects.create(
            agreement=self.agreement,
            billing_month=date(2026, 10, 1),
            rent_amount=Decimal("8000.00"),
            due_date=date(2026, 10, 5),
            amount_paid=Decimal("8000.00"),
            status="PAID",
        )

    def test_archive_month_and_electricity_rollover(self):
        from billing.services import archive_billing_month
        from electricity.models import MeterReading

        # Archive October 2026
        result = archive_billing_month(
            owner=self.user,
            billing_month="2026-10-01",
            notes="October complete",
        )

        archive = result["archive"]
        self.assertIsNotNone(archive)
        self.assertEqual(archive.billing_month, date(2026, 10, 1))
        self.assertEqual(archive.total_tenants, 1)
        self.assertEqual(archive.total_billed, Decimal("8500.00")) # 8000 rent + 500 elec
        self.assertEqual(archive.total_paid, Decimal("8500.00"))
        self.assertEqual(archive.total_balance, Decimal("0.00"))

        # Verify rent record is marked archived
        self.rent_oct.refresh_from_db()
        self.assertTrue(self.rent_oct.is_archived)
        self.assertIsNotNone(self.rent_oct.archived_at)

        # Verify electricity rollover to November 2026 (2026-11-01)
        # November's previous_reading should equal October's current_reading (150.00)
        reading_nov = MeterReading.objects.filter(
            meter=self.meter,
            reading_date=date(2026, 11, 1),
        ).first()

        self.assertIsNotNone(reading_nov)
        self.assertEqual(reading_nov.previous_reading, Decimal("150.00"))
        self.assertEqual(reading_nov.current_reading, Decimal("150.00"))

    def test_archive_api_endpoints(self):
        from rest_framework.test import APIClient
        client = APIClient()
        client.force_authenticate(user=self.user)

        # POST /api/billing/archive/
        response = client.post(
            "/api/billing/archive/",
            {"billing_month": "2026-10", "notes": "API test archive"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn("archive", response.data)
        archive_id = response.data["archive"]["id"]

        # GET /api/billing/archive/
        list_res = client.get("/api/billing/archive/")
        self.assertEqual(list_res.status_code, 200)
        self.assertTrue(len(list_res.data) >= 1)

        # GET /api/billing/archive/<id>/download/
        dl_res = client.get(f"/api/billing/archive/{archive_id}/download/")
        self.assertEqual(dl_res.status_code, 200)
        self.assertEqual(dl_res["Content-Type"], "text/csv")
        csv_text = dl_res.content.decode("utf-8")
        self.assertIn("Rahul Sharma", csv_text)
        self.assertIn("MTR-101", csv_text)

