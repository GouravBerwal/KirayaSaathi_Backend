from decimal import Decimal
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from properties.models import Property, Room
from tenants.models import Tenant, RentalAgreement
from billing.models import RentRecord
from electricity.models import ElectricityMeter, MeterReading, ElectricityBill
from payments.models import Payment

User = get_user_model()


class FullLifecycleIntegrationWorkflowTests(APITestCase):
    """
    Comprehensive End-to-End Test Suite verifying the full rental lifecycle:
    Property -> Rooms -> Tenants -> Rental Agreements -> Monthly Rent ->
    Electricity Readings -> Electricity Bills -> Payments -> Invoices ->
    Dashboard -> Owner Data Isolation.
    """

    def setUp(self):
        # Create Owner A
        self.owner_a = User.objects.create_user(
            username="owner_a",
            email="owner_a@example.com",
            password="StrongPassword!2026",
            first_name="Ramesh",
            last_name="Sharma",
        )
        # Create Owner B (for cross-owner isolation checks)
        self.owner_b = User.objects.create_user(
            username="owner_b",
            email="owner_b@example.com",
            password="StrongPassword!2026",
            first_name="Suresh",
            last_name="Verma",
        )
        self.today = timezone.localdate()
        self.billing_month = self.today.replace(day=1)

    def test_workflow_1_property_and_room_creation(self):
        """Workflow 1: Create property -> create room -> verify property details."""
        self.client.force_authenticate(user=self.owner_a)

        # 1. Create property
        prop_res = self.client.post(
            "/api/properties/",
            {
                "name": "Shanti Niwas Residency",
                "property_type": "APARTMENT",
                "address": "12/A Ring Road",
                "city": "Indore",
                "state": "Madhya Pradesh",
                "pin_code": "452001",
                "monthly_rent": "8000.00",
                "security_deposit": "16000.00",
                "rent_due_day": 5,
                "electricity_rate": "8.50",
            },
            format="json",
        )
        self.assertEqual(prop_res.status_code, status.HTTP_201_CREATED)
        prop_id = prop_res.data["id"]

        # 2. Create Room
        room_res = self.client.post(
            "/api/properties/rooms/",
            {
                "property": prop_id,
                "room_number": "101",
                "floor": 1,
                "room_type": "SINGLE",
                "monthly_rent": "8000.00",
                "security_deposit": "16000.00",
                "status": "VACANT",
            },
            format="json",
        )
        self.assertEqual(room_res.status_code, status.HTTP_201_CREATED)
        room_id = room_res.data["id"]

        # 3. Verify property detail view and rooms endpoint
        detail_res = self.client.get(f"/api/properties/{prop_id}/")
        self.assertEqual(detail_res.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_res.data["name"], "Shanti Niwas Residency")

        rooms_res = self.client.get("/api/properties/rooms/")
        self.assertEqual(rooms_res.status_code, status.HTTP_200_OK)
        prop_rooms = [r for r in rooms_res.data if r["property"] == prop_id]
        self.assertEqual(len(prop_rooms), 1)
        self.assertEqual(prop_rooms[0]["room_number"], "101")

    def test_workflow_2_tenant_and_agreement_creation(self):
        """Workflow 2: Create tenant -> create agreement -> verify room becomes OCCUPIED and conflicts are blocked."""
        self.client.force_authenticate(user=self.owner_a)

        # Create Property & Room
        prop = Property.objects.create(
            owner=self.owner_a,
            name="Green Villa",
            property_type="BUILDING",
            address="Vijay Nagar",
            city="Indore",
            state="MP",
            pin_code="452010",
            rent_due_day=5,
            electricity_rate=Decimal("8.00"),
        )
        room = Room.objects.create(
            property=prop,
            room_number="201",
            floor=2,
            room_type="SINGLE",
            monthly_rent=Decimal("6000.00"),
            security_deposit=Decimal("12000.00"),
            status="VACANT",
        )

        # 1. Create Tenant
        tenant_res = self.client.post(
            "/api/tenants/",
            {
                "full_name": "Aman Verma",
                "email": "aman@example.com",
                "phone": "9876543210",
                "address": "Permanent address Bhopal",
                "emergency_contact_name": "Father Verma",
                "emergency_contact_phone": "9876543211",
            },
            format="json",
        )
        self.assertEqual(tenant_res.status_code, status.HTTP_201_CREATED)
        tenant_id = tenant_res.data["id"]

        # 2. Create Agreement
        agr_res = self.client.post(
            "/api/tenants/rental-agreements/",
            {
                "tenant": tenant_id,
                "room": room.id,
                "start_date": self.today.isoformat(),
                "monthly_rent": "6000.00",
                "security_deposit": "12000.00",
                "status": "ACTIVE",
            },
            format="json",
        )
        self.assertEqual(agr_res.status_code, status.HTTP_201_CREATED)

        # 3. Verify duplicate active agreement on same room is rejected
        tenant2 = Tenant.objects.create(owner=self.owner_a, full_name="Rahul Jain", phone="9111111111")
        dup_agr_res = self.client.post(
            "/api/tenants/rental-agreements/",
            {
                "tenant": tenant2.id,
                "room": room.id,
                "start_date": self.today.isoformat(),
                "monthly_rent": "6000.00",
                "security_deposit": "12000.00",
                "status": "ACTIVE",
            },
            format="json",
        )
        self.assertEqual(dup_agr_res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("room", dup_agr_res.data)

    def test_workflow_3_rent_billing_and_payment_sync(self):
        """Workflow 3: Create rent record -> record payment -> verify balance and payment sync."""
        self.client.force_authenticate(user=self.owner_a)

        prop = Property.objects.create(
            owner=self.owner_a,
            name="Sunrise Heights",
            property_type="BUILDING",
            address="MG Road",
            city="Indore",
            state="MP",
            pin_code="452001",
        )
        room = Room.objects.create(
            property=prop,
            room_number="301",
            floor=3,
            room_type="SINGLE",
            monthly_rent=Decimal("7000.00"),
            security_deposit=Decimal("14000.00"),
            status="OCCUPIED",
        )
        tenant = Tenant.objects.create(owner=self.owner_a, full_name="Rohit Gupta", phone="9826012345")
        agreement = RentalAgreement.objects.create(
            tenant=tenant,
            room=room,
            start_date=self.today,
            monthly_rent=Decimal("7000.00"),
            security_deposit=Decimal("14000.00"),
            status="ACTIVE",
        )

        # 1. Create Rent Record
        rent_res = self.client.post(
            "/api/billing/",
            {
                "agreement": agreement.id,
                "billing_month": self.billing_month.isoformat(),
                "rent_amount": "7000.00",
                "due_date": (self.billing_month + timedelta(days=5)).isoformat(),
                "notes": "Monthly rent",
            },
            format="json",
        )
        self.assertEqual(rent_res.status_code, status.HTTP_201_CREATED)
        rent_record_id = rent_res.data["id"]

        # 2. Record Partial Payment (₹3000)
        pay_res1 = self.client.post(
            "/api/payments/",
            {
                "agreement": agreement.id,
                "rent_record": rent_record_id,
                "electricity_bill": None,
                "amount": "3000.00",
                "payment_date": timezone.now().isoformat(),
                "payment_method": "UPI",
                "status": "COMPLETED",
                "transaction_reference": "UTR12345678",
                "notes": "Partial rent payment",
            },
            format="json",
        )
        self.assertEqual(pay_res1.status_code, status.HTTP_201_CREATED)

        # Verify RentRecord status is PARTIAL and amount_paid is 3000
        rent_rec = RentRecord.objects.get(pk=rent_record_id)
        self.assertEqual(rent_rec.amount_paid, Decimal("3000.00"))
        self.assertEqual(rent_rec.status, "PARTIAL")

        # 3. Record Remaining Payment (₹4000)
        pay_res2 = self.client.post(
            "/api/payments/",
            {
                "agreement": agreement.id,
                "rent_record": rent_record_id,
                "electricity_bill": None,
                "amount": "4000.00",
                "payment_date": timezone.now().isoformat(),
                "payment_method": "UPI",
                "status": "COMPLETED",
                "transaction_reference": "UTR12345679",
                "notes": "Full settlement",
            },
            format="json",
        )
        self.assertEqual(pay_res2.status_code, status.HTTP_201_CREATED)

        # Verify RentRecord status is now PAID
        rent_rec.refresh_from_db()
        self.assertEqual(rent_rec.amount_paid, Decimal("7000.00"))
        self.assertEqual(rent_rec.status, "PAID")

    def test_workflow_4_meter_reading_and_electricity_bill_generation(self):
        """Workflow 4: Create meter reading -> generate bill -> record payment -> verify bill status."""
        self.client.force_authenticate(user=self.owner_a)

        prop = Property.objects.create(
            owner=self.owner_a,
            name="Electricity Test Villa",
            property_type="BUILDING",
            address="AB Road",
            city="Indore",
            state="MP",
            pin_code="452001",
            rent_due_day=5,
            electricity_rate=Decimal("10.00"),
        )
        room = Room.objects.create(
            property=prop,
            room_number="401",
            floor=4,
            room_type="SINGLE",
            monthly_rent=Decimal("5000.00"),
            security_deposit=Decimal("10000.00"),
            status="OCCUPIED",
        )
        tenant = Tenant.objects.create(owner=self.owner_a, full_name="Pooja Sharma", phone="9876500000")
        agreement = RentalAgreement.objects.create(
            tenant=tenant,
            room=room,
            start_date=self.today,
            monthly_rent=Decimal("5000.00"),
            security_deposit=Decimal("10000.00"),
            status="ACTIVE",
        )

        meter = ElectricityMeter.objects.create(
            room=room,
            meter_number="MTR-401-TEST",
            installation_date=self.today,
            is_active=True,
        )

        # 1. Post Meter Reading (prev 100, curr 250 => 150 units @ ₹10 = ₹1500)
        reading_res = self.client.post(
            "/api/electricity/readings/",
            {
                "meter": meter.id,
                "reading_date": self.today.isoformat(),
                "previous_reading": "100.00",
                "current_reading": "250.00",
                "notes": "October meter reading",
            },
            format="json",
        )
        self.assertEqual(reading_res.status_code, status.HTTP_201_CREATED)
        reading_id = reading_res.data["id"]

        # 2. Generate Electricity Bill
        gen_res = self.client.post(
            "/api/electricity/bills/generate/",
            {"reading_id": reading_id},
            format="json",
        )
        self.assertIn(gen_res.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        self.assertTrue(gen_res.data["created"])
        bill_id = gen_res.data["bill_id"]

        bill = ElectricityBill.objects.get(pk=bill_id)
        self.assertEqual(bill.units_consumed, Decimal("150.00"))
        self.assertEqual(bill.total_amount, Decimal("1500.00"))
        self.assertIn(bill.status, ["PENDING", "OVERDUE"])

        # 3. Pay Electricity Bill
        pay_res = self.client.post(
            "/api/payments/",
            {
                "agreement": agreement.id,
                "rent_record": None,
                "electricity_bill": bill.id,
                "amount": "1500.00",
                "payment_date": timezone.now().isoformat(),
                "payment_method": "UPI",
                "status": "COMPLETED",
                "transaction_reference": "ELEC-UTR-9999",
                "notes": "Electricity bill payment",
            },
            format="json",
        )
        self.assertEqual(pay_res.status_code, status.HTTP_201_CREATED)

        bill.refresh_from_db()
        self.assertEqual(bill.amount_paid, Decimal("1500.00"))
        self.assertEqual(bill.status, "PAID")

    def test_workflow_5_dashboard_metrics_consistency(self):
        """Workflow 5: Dashboard returns real aggregated metrics from the database."""
        self.client.force_authenticate(user=self.owner_a)

        prop = Property.objects.create(
            owner=self.owner_a,
            name="Dashboard Test House",
            property_type="BUILDING",
            address="Palasia",
            city="Indore",
            state="MP",
            pin_code="452001",
        )
        room = Room.objects.create(
            property=prop,
            room_number="D101",
            floor=1,
            room_type="SINGLE",
            monthly_rent=Decimal("5000.00"),
            security_deposit=Decimal("10000.00"),
            status="OCCUPIED",
        )

        res = self.client.get("/api/dashboard/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("rooms", res.data)
        self.assertEqual(res.data["rooms"]["total"], 1)
        self.assertEqual(res.data["rooms"]["occupied"], 1)

    def test_workflow_6_unauthenticated_access_is_blocked(self):
        """Workflow 6: Logged out users cannot access protected APIs."""
        self.client.logout()

        endpoints = [
            "/api/properties/",
            "/api/properties/rooms/",
            "/api/tenants/",
            "/api/tenants/rental-agreements/",
            "/api/billing/",
            "/api/electricity/meters/",
            "/api/electricity/bills/",
            "/api/payments/",
            "/api/dashboard/",
            "/api/reports/",
        ]
        for ep in endpoints:
            res = self.client.get(ep)
            self.assertIn(
                res.status_code,
                [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
                f"Endpoint {ep} allowed unauthenticated access!",
            )

    def test_workflow_7_cross_owner_data_isolation(self):
        """Workflow 7: Owner B cannot see or manipulate Owner A's properties, tenants, rooms, or bills."""
        # Owner A creates records
        prop_a = Property.objects.create(
            owner=self.owner_a,
            name="Owner A Property",
            property_type="BUILDING",
            address="Owner A Address",
            city="Indore",
            state="MP",
            pin_code="452001",
        )
        room_a = Room.objects.create(
            property=prop_a,
            room_number="A1",
            floor=1,
            room_type="SINGLE",
            monthly_rent=Decimal("5000.00"),
            security_deposit=Decimal("10000.00"),
            status="OCCUPIED",
        )
        tenant_a = Tenant.objects.create(
            owner=self.owner_a,
            full_name="Owner A Tenant",
            phone="9876543210",
        )

        # Authenticate as Owner B
        self.client.force_authenticate(user=self.owner_b)

        # 1. Owner B list should NOT contain Owner A's property
        b_props = self.client.get("/api/properties/")
        self.assertEqual(b_props.status_code, status.HTTP_200_OK)
        self.assertEqual(len(b_props.data), 0)

        # 2. Owner B GET detail of Owner A's property returns 404
        b_prop_detail = self.client.get(f"/api/properties/{prop_a.id}/")
        self.assertEqual(b_prop_detail.status_code, status.HTTP_404_NOT_FOUND)

        # 3. Owner B cannot edit Owner A's property
        b_patch = self.client.patch(
            f"/api/properties/{prop_a.id}/",
            {"name": "Hacked Name"},
            format="json",
        )
        self.assertEqual(b_patch.status_code, status.HTTP_404_NOT_FOUND)

        # 4. Owner B cannot see Owner A's tenant
        b_tenants = self.client.get("/api/tenants/")
        self.assertEqual(b_tenants.status_code, status.HTTP_200_OK)
        self.assertEqual(len(b_tenants.data), 0)

        b_tenant_detail = self.client.get(f"/api/tenants/{tenant_a.id}/")
        self.assertEqual(b_tenant_detail.status_code, status.HTTP_404_NOT_FOUND)

        # 5. Owner B's dashboard shows 0 rooms
        b_dash = self.client.get("/api/dashboard/")
        self.assertEqual(b_dash.status_code, status.HTTP_200_OK)
        self.assertEqual(b_dash.data["rooms"]["total"], 0)

    def test_workflow_8_property_update_propagates_dynamically(self):
        """Workflow 8: Property update immediately propagates across rooms, agreements, billing, electricity, and payments."""
        self.client.force_authenticate(user=self.owner_a)

        # 1. Create property
        prop = Property.objects.create(
            owner=self.owner_a,
            name="Original Heights",
            property_type="BUILDING",
            address="Sector 14",
            city="Jaipur",
        )
        room = Room.objects.create(
            property=prop,
            room_number="101",
            floor=1,
            room_type="SINGLE",
            monthly_rent=Decimal("8000.00"),
            security_deposit=Decimal("16000.00"),
            status="OCCUPIED",
        )
        tenant = Tenant.objects.create(
            owner=self.owner_a,
            full_name="Vikas Kumar",
            phone="9876543210",
        )
        agreement = RentalAgreement.objects.create(
            tenant=tenant,
            room=room,
            start_date=self.today,
            monthly_rent=Decimal("8000.00"),
            security_deposit=Decimal("16000.00"),
            status="ACTIVE",
        )
        rent_record = RentRecord.objects.create(
            agreement=agreement,
            billing_month=self.billing_month,
            rent_amount=Decimal("8000.00"),
            due_date=self.today + timedelta(days=5),
        )
        meter = ElectricityMeter.objects.create(
            room=room,
            meter_number="MTR-999",
            installation_date=self.today,
        )
        reading = MeterReading.objects.create(
            meter=meter,
            reading_date=self.today,
            previous_reading=Decimal("100.00"),
            current_reading=Decimal("200.00"),
        )
        bill = ElectricityBill.objects.create(
            meter=meter,
            reading=reading,
            billing_month=self.billing_month,
            units_consumed=Decimal("100.00"),
            rate_per_unit=Decimal("8.00"),
            total_amount=Decimal("800.00"),
            due_date=self.today + timedelta(days=5),
        )
        payment = Payment.objects.create(
            agreement=agreement,
            rent_record=rent_record,
            amount=Decimal("8000.00"),
            payment_date=timezone.now(),
            payment_method="UPI",
            status="COMPLETED",
        )

        # 2. Update property name
        patch_res = self.client.patch(
            f"/api/properties/{prop.id}/",
            {"name": "Royal Emerald Heights"},
            format="json",
        )
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_res.data["name"], "Royal Emerald Heights")

        # 3. Verify Rooms endpoint reflects the updated property name
        rooms_res = self.client.get("/api/properties/rooms/")
        self.assertEqual(rooms_res.status_code, status.HTTP_200_OK)
        matched_room = next(r for r in rooms_res.data if r["id"] == room.id)
        self.assertEqual(matched_room["property"], prop.id)

        # 4. Verify Billing (RentRecord) reflects updated property_name and property_id
        billing_res = self.client.get("/api/billing/")
        self.assertEqual(billing_res.status_code, status.HTTP_200_OK)
        matched_rent = next(r for r in billing_res.data if r["id"] == rent_record.id)
        self.assertEqual(matched_rent["property_name"], "Royal Emerald Heights")
        self.assertEqual(matched_rent["property_id"], prop.id)

        # 5. Verify Rental Agreements reflect updated property_name and property_id
        agr_res = self.client.get("/api/tenants/rental-agreements/")
        self.assertEqual(agr_res.status_code, status.HTTP_200_OK)
        matched_agr = next(a for a in agr_res.data if a["id"] == agreement.id)
        self.assertEqual(matched_agr["property_name"], "Royal Emerald Heights")
        self.assertEqual(matched_agr["property_id"], prop.id)

        # 6. Verify Payments reflect updated property_name and property_id
        pay_res = self.client.get("/api/payments/")
        self.assertEqual(pay_res.status_code, status.HTTP_200_OK)
        matched_pay = next(p for p in pay_res.data if p["id"] == payment.id)
        self.assertEqual(matched_pay["property_name"], "Royal Emerald Heights")
        self.assertEqual(matched_pay["property_id"], prop.id)

        # 7. Verify Electricity Bills reflect updated property_name and property_id
        elec_res = self.client.get("/api/electricity/bills/")
        self.assertEqual(elec_res.status_code, status.HTTP_200_OK)
        matched_bill = next(b for b in elec_res.data if b["id"] == bill.id)
        self.assertEqual(matched_bill["property_name"], "Royal Emerald Heights")
        self.assertEqual(matched_bill["property_id"], prop.id)

    def test_workflow_9_room_sharing_capacity_enforcement_and_split_billing(self):
        """Workflow 9: Room sharing capacity (Single=1, Double=2, Triple=3) enforced and bills split accordingly."""
        self.client.force_authenticate(user=self.owner_a)

        prop = Property.objects.create(
            owner=self.owner_a,
            name="Sharing Residency",
            property_type="PG",
            address="Ring Road",
            city="Indore",
            electricity_rate=Decimal("10.00"),
            rent_due_day=5,
        )

        # 1. Single Room: capacity = 1
        single_room = Room.objects.create(
            property=prop,
            room_number="S-101",
            floor="1",
            room_type="SINGLE",
            monthly_rent=Decimal("6000.00"),
            security_deposit=Decimal("12000.00"),
        )
        self.assertEqual(single_room.capacity, 1)

        t1 = Tenant.objects.create(owner=self.owner_a, full_name="Tenant Single", phone="9999900001")
        t2 = Tenant.objects.create(owner=self.owner_a, full_name="Tenant Over Single", phone="9999900002")

        # Assign 1st tenant to Single Room -> Success
        ag1_res = self.client.post(
            "/api/tenants/rental-agreements/",
            {
                "tenant": t1.id,
                "room": single_room.id,
                "start_date": str(self.today),
                "monthly_rent": "6000.00",
                "security_deposit": "12000.00",
                "status": "ACTIVE",
            },
            format="json",
        )
        self.assertEqual(ag1_res.status_code, status.HTTP_201_CREATED)

        # Assign 2nd tenant to Single Room -> MUST FAIL (capacity 1 reached)
        ag2_res = self.client.post(
            "/api/tenants/rental-agreements/",
            {
                "tenant": t2.id,
                "room": single_room.id,
                "start_date": str(self.today),
                "monthly_rent": "6000.00",
                "security_deposit": "12000.00",
                "status": "ACTIVE",
            },
            format="json",
        )
        self.assertEqual(ag2_res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("capacity", str(ag2_res.data).lower())

        # 2. Double Room: capacity = 2
        double_room = Room.objects.create(
            property=prop,
            room_number="D-201",
            floor="2",
            room_type="DOUBLE",
            monthly_rent=Decimal("5000.00"),
            security_deposit=Decimal("10000.00"),
        )
        self.assertEqual(double_room.capacity, 2)

        t3 = Tenant.objects.create(owner=self.owner_a, full_name="Tenant Double 1", phone="9999900003")
        t4 = Tenant.objects.create(owner=self.owner_a, full_name="Tenant Double 2", phone="9999900004")
        t5 = Tenant.objects.create(owner=self.owner_a, full_name="Tenant Double 3", phone="9999900005")

        # Assign 1st tenant to Double Room -> Success (1/2 beds occupied)
        d_ag1 = self.client.post(
            "/api/tenants/rental-agreements/",
            {
                "tenant": t3.id,
                "room": double_room.id,
                "start_date": str(self.today),
                "monthly_rent": "5000.00",
                "security_deposit": "10000.00",
                "status": "ACTIVE",
            },
            format="json",
        )
        self.assertEqual(d_ag1.status_code, status.HTTP_201_CREATED)

        # Check Room details via API
        rooms_res = self.client.get("/api/properties/rooms/")
        d_room_api = next(r for r in rooms_res.data if r["id"] == double_room.id)
        self.assertEqual(d_room_api["capacity"], 2)
        self.assertEqual(d_room_api["occupied_beds"], 1)
        self.assertEqual(d_room_api["vacant_beds"], 1)
        self.assertFalse(d_room_api["is_full"])

        # Assign 2nd tenant to Double Room -> Success (2/2 beds occupied, now FULL)
        d_ag2 = self.client.post(
            "/api/tenants/rental-agreements/",
            {
                "tenant": t4.id,
                "room": double_room.id,
                "start_date": str(self.today),
                "monthly_rent": "5000.00",
                "security_deposit": "10000.00",
                "status": "ACTIVE",
            },
            format="json",
        )
        self.assertEqual(d_ag2.status_code, status.HTTP_201_CREATED)

        # Check Room details again -> is_full must now be True
        rooms_res = self.client.get("/api/properties/rooms/")
        d_room_api = next(r for r in rooms_res.data if r["id"] == double_room.id)
        self.assertEqual(d_room_api["occupied_beds"], 2)
        self.assertEqual(d_room_api["vacant_beds"], 0)
        self.assertTrue(d_room_api["is_full"])
        self.assertEqual(len(d_room_api["occupants"]), 2)

        # Assign 3rd tenant to Double Room -> MUST FAIL
        d_ag3 = self.client.post(
            "/api/tenants/rental-agreements/",
            {
                "tenant": t5.id,
                "room": double_room.id,
                "start_date": str(self.today),
                "monthly_rent": "5000.00",
                "security_deposit": "10000.00",
                "status": "ACTIVE",
            },
            format="json",
        )
        self.assertEqual(d_ag3.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("capacity", str(d_ag3.data).lower())

        # 3. Electricity Bill Split across Double Room
        meter = ElectricityMeter.objects.create(
            room=double_room,
            meter_number="MTR-D201",
            installation_date=self.today,
        )
        reading = MeterReading.objects.create(
            meter=meter,
            reading_date=self.today,
            previous_reading=Decimal("100.00"),
            current_reading=Decimal("180.00"),
        )
        bill = ElectricityBill.objects.create(
            meter=meter,
            reading=reading,
            billing_month=self.billing_month,
            units_consumed=Decimal("80.00"),
            rate_per_unit=Decimal("10.00"),
            total_amount=Decimal("800.00"),
            due_date=self.today + timedelta(days=5),
        )

        # Electricity bills API should return split info (50% each for twin sharing)
        bills_res = self.client.get("/api/electricity/bills/")
        self.assertEqual(bills_res.status_code, status.HTTP_200_OK)
        matched_bill = next(b for b in bills_res.data if b["id"] == bill.id)
        self.assertEqual(matched_bill["split_count"], 2)
        self.assertEqual(matched_bill["split_amount"], 400.0)
        self.assertEqual(matched_bill["split_units"], 40.0)
        self.assertEqual(len(matched_bill["occupants"]), 2)

    def test_workflow_10_rent_record_status_toggle_and_live_payment_sync(self):
        """Workflow 10: Toggling rent record status to PAID/PENDING live-syncs payments and dashboard financials."""
        self.client.force_authenticate(user=self.owner_a)

        prop = Property.objects.create(
            owner=self.owner_a,
            name="Financial Sync Heights",
            address="Palasia",
            city="Indore",
        )
        room = Room.objects.create(
            property=prop,
            room_number="R-501",
            floor="5",
            room_type="SINGLE",
            monthly_rent=Decimal("15000.00"),
            security_deposit=Decimal("30000.00"),
        )
        tenant = Tenant.objects.create(
            owner=self.owner_a,
            full_name="Aakash Verma",
            phone="9826012345",
        )
        agreement = RentalAgreement.objects.create(
            tenant=tenant,
            room=room,
            start_date=self.today,
            monthly_rent=Decimal("15000.00"),
            security_deposit=Decimal("30000.00"),
            status="ACTIVE",
        )
        rent_record = RentRecord.objects.create(
            agreement=agreement,
            billing_month=self.billing_month,
            rent_amount=Decimal("15000.00"),
            amount_paid=Decimal("0.00"),
            due_date=self.today + timedelta(days=5),
            status="PENDING",
        )

        # 1. Toggle status to PAID
        patch_paid = self.client.patch(
            f"/api/billing/{rent_record.id}/",
            {"status": "PAID"},
            format="json",
        )
        self.assertEqual(patch_paid.status_code, status.HTTP_200_OK)
        rent_record.refresh_from_db()
        self.assertEqual(rent_record.status, "PAID")
        self.assertEqual(rent_record.amount_paid, Decimal("15000.00"))

        # Check Payment auto-created
        completed_payment = Payment.objects.filter(rent_record=rent_record, status="COMPLETED").first()
        self.assertIsNotNone(completed_payment)
        self.assertEqual(completed_payment.amount, Decimal("15000.00"))

        # Verify payments endpoint reflects this
        pay_res = self.client.get("/api/payments/")
        self.assertEqual(pay_res.status_code, status.HTTP_200_OK)
        self.assertTrue(any(p["id"] == completed_payment.id for p in pay_res.data))

        # 2. Toggle status back to PENDING
        patch_pending = self.client.patch(
            f"/api/billing/{rent_record.id}/",
            {"status": "PENDING"},
            format="json",
        )
        self.assertEqual(patch_pending.status_code, status.HTTP_200_OK)
        rent_record.refresh_from_db()
        self.assertEqual(rent_record.status, "PENDING")
        self.assertEqual(rent_record.amount_paid, Decimal("0.00"))
        self.assertFalse(Payment.objects.filter(rent_record=rent_record, status="COMPLETED").exists())
