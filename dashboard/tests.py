
from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status

from properties.models import Property, Room
from tenants.models import Tenant, RentalAgreement
from billing.models import RentRecord, BillingArchive
from electricity.models import (
    ElectricityMeter,
    MeterReading,
    ElectricityBill,
)
from payments.models import Payment
from .views import DashboardSummaryAPIView



User = get_user_model()

class DashboardSummaryTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="test_owner", email="test-owner@example.com",
            password="StrongTestPassword!2026",
        )
        today = timezone.localdate()

        self.property = Property.objects.create(
            owner=self.user,
            name="Dashboard Test Hostel",
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
            room_number="D101",
            floor=1,
            room_type="SINGLE",
            monthly_rent=5000,
            security_deposit=5000,
            status="OCCUPIED",
        )

        self.tenant = Tenant.objects.create(
            owner=self.user,
            full_name="Dashboard Test Tenant",
            phone="9999999999",
        )

        self.agreement = RentalAgreement.objects.create(
            tenant=self.tenant,
            room=self.room,
            start_date=today,
            monthly_rent=Decimal("5000.00"),
            security_deposit=Decimal("5000.00"),
            status="ACTIVE",
        )

        self.rent_record = RentRecord.objects.create(
            agreement=self.agreement,
            billing_month=today.replace(day=1),
            rent_amount=Decimal("5000.00"),
            due_date=today,
            amount_paid=Decimal("1000.00"),
            status="PARTIAL",
        )

        self.meter = ElectricityMeter.objects.create(
            room=self.room,
            meter_number="DASH-METER-101",
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
            amount_paid=Decimal("100.00"),
            status="PARTIAL",
        )

        self.factory = APIRequestFactory()

    def get_dashboard_response(self):
        request = self.factory.get("/api/dashboard/")
        force_authenticate(request, user=self.user)
        view = DashboardSummaryAPIView.as_view()
        return view(request)

    def test_dashboard_returns_success(self):
        response = self.get_dashboard_response()

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_room_and_tenant_counts(self):
        response = self.get_dashboard_response()
        data = response.data

        self.assertEqual(data["rooms"]["total"], 1)
        self.assertEqual(data["rooms"]["occupied"], 1)
        self.assertEqual(data["tenants"]["active"], 1)
        self.assertEqual(data["tenants"]["active_agreements"], 1)

    def test_pending_rent_is_calculated(self):
        response = self.get_dashboard_response()

        self.assertEqual(
            response.data["rent"]["pending_amount"],
            "4000.00",
        )

    def test_pending_electricity_is_calculated(self):
        response = self.get_dashboard_response()

        self.assertEqual(
            response.data["electricity"]["pending_amount"],
            "300.00",
        )

    def test_payment_summary_is_returned(self):
        Payment.objects.create(
            agreement=self.agreement,
            rent_record=self.rent_record,
            amount=Decimal("500.00"),
            payment_date=timezone.now(),
            payment_method="UPI",
            status="COMPLETED",
        )

        response = self.get_dashboard_response()

        self.assertEqual(
            response.data["payments"]["completed_payment_count"],
            1,
        )
        self.assertEqual(
            response.data["payments"]["total_collected"],
            "500.00",
        )
        self.assertEqual(len(response.data["payments"]["recent"]), 1)

    def test_income_chart_rolls_over_on_month_archive(self):
        today = timezone.localdate()
        current_m = today.replace(day=1)
        if current_m.month == 12:
            next_m = current_m.replace(year=current_m.year + 1, month=1)
        else:
            next_m = current_m.replace(month=current_m.month + 1)

        # Archive current month
        self.rent_record.is_archived = True
        self.rent_record.save(update_fields=["is_archived"])

        BillingArchive.objects.create(
            owner=self.user,
            billing_month=current_m,
            property=self.property,
            total_tenants=1,
            total_billed=Decimal("5000.00"),
            total_paid=Decimal("1000.00"),
            total_balance=Decimal("4000.00"),
            snapshot_data=[],
        )

        # New month rent record generated upon archiving
        RentRecord.objects.create(
            agreement=self.agreement,
            billing_month=next_m,
            rent_amount=Decimal("5000.00"),
            due_date=next_m.replace(day=5),
            amount_paid=Decimal("0.00"),
            status="PENDING",
            is_archived=False,
        )

        response = self.get_dashboard_response()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        months = response.data["income_chart"]["months"]
        self.assertEqual(len(months), 6)

        latest_month = months[-1]
        self.assertEqual(latest_month["month"], next_m.strftime("%b"))
        self.assertEqual(latest_month["year"], next_m.year)
        self.assertEqual(latest_month["expected"], "5000.00")
        self.assertEqual(latest_month["collected"], "0.00")

    def test_income_chart_updates_when_new_month_rent_paid(self):
        today = timezone.localdate()
        current_m = today.replace(day=1)
        if current_m.month == 12:
            next_m = current_m.replace(year=current_m.year + 1, month=1)
        else:
            next_m = current_m.replace(month=current_m.month + 1)

        self.rent_record.is_archived = True
        self.rent_record.save(update_fields=["is_archived"])

        new_rec = RentRecord.objects.create(
            agreement=self.agreement,
            billing_month=next_m,
            rent_amount=Decimal("5000.00"),
            due_date=next_m.replace(day=5),
            amount_paid=Decimal("5000.00"),
            status="PAID",
            is_archived=False,
        )

        response = self.get_dashboard_response()
        months = response.data["income_chart"]["months"]
        latest_month = months[-1]

        self.assertEqual(latest_month["month"], next_m.strftime("%b"))
        self.assertEqual(latest_month["collected"], "5000.00")
        self.assertEqual(latest_month["expected"], "5000.00")

    def test_unauthenticated_request_is_blocked(self):
        request = self.factory.get("/api/dashboard/")
        view = DashboardSummaryAPIView.as_view()
        response = view(request)
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_empty_owner_dashboard_returns_zeros(self):
        empty_owner = User.objects.create_user(
            username="empty_owner",
            email="empty-owner@example.com",
            password="StrongPassword!2026",
        )
        request = self.factory.get("/api/dashboard/")
        force_authenticate(request, user=empty_owner)
        view = DashboardSummaryAPIView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data["rooms"]["total"], 0)
        self.assertEqual(data["rooms"]["occupied"], 0)
        self.assertEqual(data["rooms"]["vacant"], 0)
        self.assertEqual(data["rent"]["current_month_collected"], "0.00")
        self.assertEqual(data["electricity"]["current_month_collected"], "0.00")
        self.assertEqual(len(data["payments"]["recent"]), 0)

    def test_cross_owner_isolation_in_dashboard(self):
        owner_b = User.objects.create_user(
            username="owner_b",
            email="owner-b@example.com",
            password="StrongPassword!2026",
        )
        request = self.factory.get("/api/dashboard/")
        force_authenticate(request, user=owner_b)
        view = DashboardSummaryAPIView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        # Owner B must see 0 rooms and 0 rent even though Owner A (self.user) has active rooms and rent
        self.assertEqual(data["rooms"]["total"], 0)
        self.assertEqual(data["rent"]["current_month_collected"], "0.00")
        self.assertEqual(data["payments"]["completed_payment_count"], 0)

    def test_reconciled_pending_rent_is_zero_when_fully_paid(self):
        self.rent_record.amount_paid = Decimal("5000.00")
        self.rent_record.status = "PAID"
        self.rent_record.save(update_fields=["amount_paid", "status"])

        response = self.get_dashboard_response()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["rent"]["current_month_collected"], "5000.00")
        self.assertEqual(response.data["rent"]["current_month_pending"], "0.00")

    def test_reconciled_pending_electricity_is_zero_when_fully_paid(self):
        self.electricity_bill.amount_paid = Decimal("400.00")
        self.electricity_bill.status = "PAID"
        self.electricity_bill.save(update_fields=["amount_paid", "status"])

        response = self.get_dashboard_response()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["electricity"]["current_month_collected"], "400.00")
        self.assertEqual(response.data["electricity"]["current_month_pending"], "0.00")

    def test_due_date_none_handled_gracefully(self):
        from .views import calculate_bill_summary
        mock_records = RentRecord.objects.filter(pk=self.rent_record.pk)
        summary = calculate_bill_summary(mock_records, "rent_amount")
        self.assertIn("pending_amount", summary)
        self.assertIn("overdue_amount", summary)


