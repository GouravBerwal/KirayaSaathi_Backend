
from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from properties.models import Property, Room
from tenants.models import Tenant, RentalAgreement
from billing.models import RentRecord
from electricity.models import (
    ElectricityMeter,
    MeterReading,
    ElectricityBill,
)
from payments.models import Payment
from payments.serializers import PaymentSerializer
from payments.views import (
    PaymentListCreateAPIView,
    PaymentDetailAPIView,
)



User = get_user_model()

class PaymentSerializerTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="test_owner", email="test-owner@example.com",
            password="StrongTestPassword!2026",
        )
        today = date.today()

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
            room_number="T101",
            floor=1,
            room_type="SINGLE",
            monthly_rent=5000,
            security_deposit=5000,
            status="OCCUPIED",
        )

        self.tenant = Tenant.objects.create(
            owner=self.user,
            full_name="Test Tenant",
            phone="9999999999",
        )

        self.agreement = RentalAgreement.objects.create(
            tenant=self.tenant,
            room=self.room,
            start_date=today,
            monthly_rent=5000,
            security_deposit=5000,
            status="ACTIVE",
        )

        self.rent_record = RentRecord.objects.create(
            agreement=self.agreement,
            billing_month=today.replace(day=1),
            rent_amount=Decimal("5000.00"),
            due_date=today,
            amount_paid=Decimal("0.00"),
            status="PENDING",
        )

        self.meter = ElectricityMeter.objects.create(
            room=self.room,
            meter_number="TEST-METER-101",
            installation_date=today,
            is_active=True,
        )

        self.reading = MeterReading.objects.create(
            meter=self.meter,
            reading_date=today,
            previous_reading=Decimal("100.00"),
            current_reading=Decimal("150.00"),
        )

        self.electricity_bill = ElectricityBill.objects.create(
            meter=self.meter,
            reading=self.reading,
            billing_month=today.replace(day=1),
            units_consumed=Decimal("50.00"),
            rate_per_unit=Decimal("8.00"),
            total_amount=Decimal("400.00"),
            due_date=today,
            amount_paid=Decimal("0.00"),
            status="PENDING",
        )

    def valid_payment_data(self):
        return {
            "agreement": self.agreement.pk,
            "rent_record": self.rent_record.pk,
            "amount": "1000.00",
            "payment_date": timezone.now().isoformat(),
            "payment_method": "UPI",
            "status": "COMPLETED",
        }

    def create_payment_through_view(self, data):
        serializer = PaymentSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        PaymentListCreateAPIView().perform_create(serializer)

        return serializer.instance

    # Existing serializer tests

    def test_valid_rent_payment(self):
        serializer = PaymentSerializer(
            data=self.valid_payment_data()
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_zero_amount_is_rejected(self):
        data = self.valid_payment_data()
        data["amount"] = "0.00"

        serializer = PaymentSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("amount", serializer.errors)

    def test_payment_without_bill_is_rejected(self):
        data = self.valid_payment_data()
        data.pop("rent_record")

        serializer = PaymentSerializer(data=data)

        self.assertFalse(serializer.is_valid())

    def test_payment_with_both_bill_types_is_rejected(self):
        data = self.valid_payment_data()
        data["electricity_bill"] = self.electricity_bill.pk

        serializer = PaymentSerializer(data=data)

        self.assertFalse(serializer.is_valid())

    # Payment reconciliation tests

    def test_partial_rent_payment_updates_bill(self):
        self.create_payment_through_view(
            self.valid_payment_data()
        )

        self.rent_record.refresh_from_db()

        self.assertEqual(
            self.rent_record.amount_paid,
            Decimal("1000.00"),
        )
        self.assertEqual(self.rent_record.status, "PARTIAL")

    def test_full_rent_payment_marks_bill_paid(self):
        data = self.valid_payment_data()
        data["amount"] = "5000.00"

        self.create_payment_through_view(data)

        self.rent_record.refresh_from_db()

        self.assertEqual(
            self.rent_record.amount_paid,
            Decimal("5000.00"),
        )
        self.assertEqual(self.rent_record.status, "PAID")

    def test_failed_payment_does_not_change_bill_balance(self):
        data = self.valid_payment_data()
        data["status"] = "FAILED"

        self.create_payment_through_view(data)

        self.rent_record.refresh_from_db()

        self.assertEqual(
            self.rent_record.amount_paid,
            Decimal("0.00"),
        )
        self.assertEqual(self.rent_record.status, "PENDING")

    def test_deleting_payment_recalculates_bill(self):
        payment = self.create_payment_through_view(
            self.valid_payment_data()
        )

        self.rent_record.refresh_from_db()
        self.assertEqual(
            self.rent_record.amount_paid,
            Decimal("1000.00"),
        )

        PaymentDetailAPIView().perform_destroy(payment)

        self.rent_record.refresh_from_db()

        self.assertEqual(
            self.rent_record.amount_paid,
            Decimal("0.00"),
        )
        self.assertEqual(self.rent_record.status, "PENDING")

    def test_updating_payment_recalculates_bill(self):
        payment = self.create_payment_through_view(
            self.valid_payment_data()
        )

        updated_data = {"amount": "2000.00"}

        serializer = PaymentSerializer(
            payment,
            data=updated_data,
            partial=True,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

        PaymentDetailAPIView().perform_update(serializer)

        self.rent_record.refresh_from_db()

        self.assertEqual(
            self.rent_record.amount_paid,
            Decimal("2000.00"),
        )
        self.assertEqual(self.rent_record.status, "PARTIAL")

    def test_overpayment_is_rejected(self):
        data = self.valid_payment_data()
        data["amount"] = "4000.00"

        self.create_payment_through_view(data)

        extra_data = self.valid_payment_data()
        extra_data["amount"] = "1001.00"

        serializer = PaymentSerializer(data=extra_data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("amount", serializer.errors)

    def test_electricity_payment_updates_bill(self):
        data = {
            "agreement": self.agreement.pk,
            "electricity_bill": self.electricity_bill.pk,
            "amount": "200.00",
            "payment_date": timezone.now().isoformat(),
            "payment_method": "UPI",
            "status": "COMPLETED",
        }

        self.create_payment_through_view(data)

        self.electricity_bill.refresh_from_db()

        self.assertEqual(
            self.electricity_bill.amount_paid,
            Decimal("200.00"),
        )
        self.assertEqual(
            self.electricity_bill.status,
            "PARTIAL",
        )
