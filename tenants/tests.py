from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from properties.models import Property, Room
from tenants.models import Tenant, RentalAgreement


class RentalAgreementUpdateTestCase(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="testowner",
            password="testpassword123",
            email="owner@example.com",
        )
        self.client.force_authenticate(user=self.user)

        self.property = Property.objects.create(
            owner=self.user,
            name="Sunrise PG",
            property_type="PG",
            address="123 Street",
            city="Indore",
            state="Madhya Pradesh",
            pin_code="452001",
            monthly_rent=Decimal("6000.00"),
            security_deposit=Decimal("12000.00"),
            rent_due_day=5,
        )

        self.room = Room.objects.create(
            property=self.property,
            room_number="101",
            floor="1",
            room_type="SINGLE",
            status="OCCUPIED",
            monthly_rent=Decimal("6000.00"),
            security_deposit=Decimal("12000.00"),
        )

        self.tenant = Tenant.objects.create(
            owner=self.user,
            full_name="Rahul Verma",
            phone="9876543210",
            email="rahul@example.com",
            address="Permanent Address",
            emergency_contact_name="Father",
            emergency_contact_phone="9876543211",
        )

        self.agreement = RentalAgreement.objects.create(
            tenant=self.tenant,
            room=self.room,
            start_date="2026-10-01",
            monthly_rent=Decimal("6000.00"),
            security_deposit=Decimal("12000.00"),
            status="ACTIVE",
        )

    def test_patch_rental_agreement_does_not_raise_attribute_error(self):
        url = reverse("rental-agreement-detail", kwargs={"pk": self.agreement.pk})
        response = self.client.patch(
            url,
            {
                "monthly_rent": "6500.00",
                "notes": "Updated rent",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.agreement.refresh_from_db()
        self.assertEqual(self.agreement.monthly_rent, Decimal("6500.00"))
        self.assertEqual(self.agreement.notes, "Updated rent")

    def test_update_tenant_mobile_and_agreement(self):
        tenant_url = reverse("tenant-detail", kwargs={"pk": self.tenant.pk})
        tenant_res = self.client.patch(
            tenant_url,
            {"phone": "9998887776"},
            format="json",
        )
        self.assertEqual(tenant_res.status_code, status.HTTP_200_OK)
        self.tenant.refresh_from_db()
        self.assertEqual(self.tenant.phone, "9998887776")

        agreement_url = reverse("rental-agreement-detail", kwargs={"pk": self.agreement.pk})
        agr_res = self.client.patch(
            agreement_url,
            {"status": "ACTIVE"},
            format="json",
        )
        self.assertEqual(agr_res.status_code, status.HTTP_200_OK)

    def test_security_deposit_list_and_update_lifecycle(self):
        # 1. Test Listing deposits
        list_url = reverse("security-deposit-list")
        res = self.client.get(list_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["security_deposit_status"], "PENDING")

        # 2. Mark security deposit as PAID with handover items
        detail_url = reverse("security-deposit-detail", kwargs={"pk": self.agreement.pk})
        items = [
            {"item": "Main Room Key", "quantity": 2, "status": "Handed Over"},
            {"item": "Almirah Key", "quantity": 1, "status": "Handed Over"},
            {"item": "Bucket & Mug", "quantity": 1, "status": "Handed Over"},
            {"item": "Ceiling Fan", "quantity": 1, "status": "Handed Over"},
        ]
        patch_res = self.client.patch(
            detail_url,
            {
                "security_deposit_status": "PAID",
                "deposit_paid_date": "2026-10-01",
                "deposit_payment_method": "UPI",
                "deposit_transaction_ref": "UPI-DEP-998811",
                "handover_items": items,
                "handover_notes": "All room assets verified in good condition.",
            },
            format="json",
        )
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)
        self.agreement.refresh_from_db()
        self.assertEqual(self.agreement.security_deposit_status, "PAID")
        self.assertEqual(len(self.agreement.handover_items), 4)
        self.assertEqual(self.agreement.deposit_transaction_ref, "UPI-DEP-998811")

        # 3. Test Exit Refund & Settlement with deduction
        refund_res = self.client.patch(
            detail_url,
            {
                "security_deposit_status": "SETTLED",
                "deposit_refund_date": "2026-11-01",
                "deduction_amount": "1500.00",
                "deduction_reason": "Room wall repainting & unreturned mug",
                "refund_amount": "10500.00",
                "handover_notes": "Tenant moved out. 2 keys returned, 1 mug missing.",
            },
            format="json",
        )
        self.assertEqual(refund_res.status_code, status.HTTP_200_OK)
        self.agreement.refresh_from_db()
        self.assertEqual(self.agreement.security_deposit_status, "SETTLED")
        self.assertEqual(self.agreement.refund_amount, Decimal("10500.00"))
        self.assertEqual(self.agreement.deduction_amount, Decimal("1500.00"))
