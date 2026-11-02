
from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status

from properties.models import Property, Room
from electricity.models import (
    ElectricityMeter,
    MeterReading,
    ElectricityBill,
)
from electricity.services import (
    calculate_units_consumed,
    calculate_electricity_amount,
    calculate_electricity_due_date,
    generate_electricity_bill,
)
from electricity.views import GenerateElectricityBillAPIView



User = get_user_model()

class ElectricityBillingTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="test_owner", email="test-owner@example.com",
            password="StrongTestPassword!2026",
        )
        self.billing_month = date(2026, 10, 1)

        self.property = Property.objects.create(
            owner=self.user,
            name="Test Hostel",
            property_type="HOSTEL",
            address="Test Road",
            city="Indore",
            state="Madhya Pradesh",
            pin_code="452001",
            monthly_rent=5000,
            security_deposit=5000,
            rent_due_day=5,
            electricity_rate=8,
        )

        self.room = Room.objects.create(
            property=self.property,
            room_number="E101",
            floor=1,
            room_type="SINGLE",
            monthly_rent=5000,
            security_deposit=5000,
            status="OCCUPIED",
        )

        self.meter = ElectricityMeter.objects.create(
            room=self.room,
            meter_number="TEST-ELECTRIC-101",
            installation_date=date(2026, 1, 1),
            is_active=True,
        )

        self.reading = MeterReading.objects.create(
            meter=self.meter,
            reading_date=date(2026, 10, 12),
            previous_reading=Decimal("100.00"),
            current_reading=Decimal("150.00"),
        )

    def test_units_consumed_calculation(self):
        units = calculate_units_consumed(
            Decimal("100.00"),
            Decimal("150.00"),
        )

        self.assertEqual(units, Decimal("50.00"))

    def test_negative_units_are_rejected(self):
        with self.assertRaises(DjangoValidationError):
            calculate_units_consumed(
                Decimal("150.00"),
                Decimal("100.00"),
            )

    def test_electricity_amount_calculation(self):
        amount = calculate_electricity_amount(
            Decimal("50.00"),
            Decimal("8.00"),
        )

        self.assertEqual(amount, Decimal("400.00"))

    def test_negative_rate_is_rejected(self):
        with self.assertRaises(DjangoValidationError):
            calculate_electricity_amount(
                Decimal("50.00"),
                Decimal("-8.00"),
            )

    def test_due_date_uses_property_due_day(self):
        due_date = calculate_electricity_due_date(
            self.billing_month,
            self.property.rent_due_day,
        )

        self.assertEqual(due_date, date(2026, 10, 5))

    def test_due_date_handles_short_month(self):
        due_date = calculate_electricity_due_date(
            date(2026, 2, 1),
            31,
        )

        self.assertEqual(due_date, date(2026, 2, 28))

    def test_electricity_bill_is_generated(self):
        bill, created = generate_electricity_bill(
            reading_id=self.reading.pk,
        )

        self.assertTrue(created)
        self.assertEqual(bill.units_consumed, Decimal("50.00"))
        self.assertEqual(bill.rate_per_unit, Decimal("8.00"))
        self.assertEqual(bill.total_amount, Decimal("400.00"))
        self.assertEqual(bill.billing_month, date(2026, 10, 1))
        self.assertEqual(bill.due_date, date(2026, 10, 5))
        self.assertEqual(bill.amount_paid, Decimal("0.00"))

    def test_duplicate_bill_is_not_created(self):
        first_bill, first_created = generate_electricity_bill(
            reading_id=self.reading.pk,
        )

        second_bill, second_created = generate_electricity_bill(
            reading_id=self.reading.pk,
        )

        self.assertTrue(first_created)
        self.assertFalse(second_created)
        self.assertEqual(first_bill.pk, second_bill.pk)
        self.assertEqual(ElectricityBill.objects.count(), 1)

    def test_inactive_meter_cannot_generate_bill(self):
        self.meter.is_active = False
        self.meter.save(update_fields=["is_active"])

        with self.assertRaises(DjangoValidationError):
            generate_electricity_bill(
                reading_id=self.reading.pk,
            )

        self.assertEqual(ElectricityBill.objects.count(), 0)

    def test_missing_reading_is_rejected(self):
        with self.assertRaises(MeterReading.DoesNotExist):
            generate_electricity_bill(reading_id=999999)

    def test_api_generates_electricity_bill(self):
        factory = APIRequestFactory()

        request = factory.post(
            "/api/electricity/bills/generate/",
            {"reading_id": self.reading.pk},
            format="json",
        )
        force_authenticate(request, user=self.user)

        view = GenerateElectricityBillAPIView.as_view()
        response = view(request)

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(response.data["created"], True)
        self.assertEqual(
            str(response.data["total_amount"]),
            "400.00",
        )

    def test_api_rejects_missing_reading_id(self):
        factory = APIRequestFactory()

        request = factory.post(
            "/api/electricity/bills/generate/",
            {},
            format="json",
        )
        force_authenticate(request, user=self.user)

        view = GenerateElectricityBillAPIView.as_view()
        response = view(request)

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
