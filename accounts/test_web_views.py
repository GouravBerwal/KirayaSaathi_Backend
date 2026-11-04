from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from properties.models import Property, Room
from tenants.models import Tenant, RentalAgreement
from billing.models import RentRecord
from electricity.models import ElectricityMeter, MeterReading, ElectricityBill
from payments.models import Payment
from notifications.models import Notification

User = get_user_model()


class WebViewsBaseTestCase(TestCase):
    def setUp(self):
        self.password = "StrongPassword@2026"
        self.owner = User.objects.create_user(
            username="test_owner",
            email="owner@kirayasaathi.app",
            password=self.password,
            first_name="Rajesh",
            last_name="Mehta",
        )
        self.client = Client()

        # Another owner for isolation tests
        self.other_owner = User.objects.create_user(
            username="other_owner",
            email="other@kirayasaathi.app",
            password=self.password,
            first_name="Vikram",
            last_name="Malhotra",
        )

        # Create sample property & room for test_owner
        self.property = Property.objects.create(
            owner=self.owner,
            name="Shanti Residency",
            property_type="BUILDING",
            address="42, 5th Main Road, HSR Layout",
            city="Bengaluru",
            state="Karnataka",
            pin_code="560102",
            monthly_rent=Decimal("12000.00"),
            security_deposit=Decimal("24000.00"),
            rent_due_day=5,
            electricity_rate=Decimal("8.00"),
        )
        self.room = Room.objects.create(
            property=self.property,
            room_number="101",
            floor="1",
            room_type="SINGLE",
            monthly_rent=Decimal("12000.00"),
            security_deposit=Decimal("24000.00"),
            status="VACANT",
        )


class AuthWebViewsTests(WebViewsBaseTestCase):
    def test_login_page_renders_ok(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sign in to your owner workspace")

    def test_register_page_renders_ok(self):
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create Owner Account")

    def test_successful_registration(self):
        response = self.client.post(reverse("register"), {
            "username": "newowner",
            "email": "newowner@kiraya.com",
            "password": "StrongPassword!2026",
            "confirm_password": "StrongPassword!2026",
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username="newowner").exists())

    def test_registration_password_mismatch_fails(self):
        response = self.client.post(reverse("register"), {
            "username": "newowner2",
            "email": "newowner2@kiraya.com",
            "password": "Password1!",
            "confirm_password": "Password2!",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Passwords do not match")
        self.assertFalse(User.objects.filter(username="newowner2").exists())

    def test_registration_duplicate_username_fails(self):
        response = self.client.post(reverse("register"), {
            "username": "test_owner",
            "email": "unique@kiraya.com",
            "password": "StrongPassword!2026",
            "confirm_password": "StrongPassword!2026",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already taken")

    def test_successful_login(self):
        response = self.client.post(reverse("login"), {
            "username": "test_owner",
            "password": self.password,
        })
        self.assertRedirects(response, reverse("dashboard"))

    def test_invalid_login(self):
        response = self.client.post(reverse("login"), {
            "username": "test_owner",
            "password": "WrongPassword",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid username/email or password.")

    def test_logout(self):
        self.client.login(username="test_owner", password=self.password)
        response = self.client.get(reverse("logout"))
        self.assertRedirects(response, reverse("login"))


class DashboardAndIsolationTests(WebViewsBaseTestCase):
    def test_unauthenticated_dashboard_redirects_to_login(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_authenticated_dashboard_renders_ok(self):
        self.client.login(username="test_owner", password=self.password)
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Shanti Residency")

    def test_owner_data_isolation(self):
        # Create other owner's property
        other_prop = Property.objects.create(
            owner=self.other_owner,
            name="Vikram Heights",
            property_type="APARTMENT",
            address="77, MG Road",
            city="Bengaluru",
            state="Karnataka",
            pin_code="560001",
            monthly_rent=Decimal("35000.00"),
            security_deposit=Decimal("70000.00"),
        )
        self.client.login(username="test_owner", password=self.password)
        response = self.client.get(reverse("dashboard"))
        self.assertNotContains(response, "Vikram Heights")

        # Other owner dashboard
        self.client.login(username="other_owner", password=self.password)
        response_other = self.client.get(reverse("dashboard"))
        self.assertContains(response_other, "Vikram Heights")
        self.assertNotContains(response_other, "Shanti Residency")


class PropertyManagementWebViewsTests(WebViewsBaseTestCase):
    def setUp(self):
        super().setUp()
        self.client.login(username="test_owner", password=self.password)

    def test_property_list_view(self):
        response = self.client.get(reverse("property_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Shanti Residency")

    def test_property_detail_view(self):
        response = self.client.get(reverse("property_detail_id", kwargs={"pk": self.property.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Shanti Residency")
        self.assertContains(response, "101")

    def test_add_property_get_and_post(self):
        response = self.client.get(reverse("add_property"))
        self.assertEqual(response.status_code, 200)

        post_response = self.client.post(reverse("add_property"), {
            "property_name": "Sunrise Enclave",
            "property_type": "APARTMENT",
            "street_address": "88, Ring Road",
            "city": "Bengaluru",
            "state": "Karnataka",
            "pin_code": "560034",
            "monthly_rent": "15000",
            "security_deposit": "30000",
            "rent_due_day": "5",
            "electricity_rate": "8.5",
        })
        self.assertRedirects(post_response, reverse("property_list"))
        self.assertTrue(Property.objects.filter(name="Sunrise Enclave", owner=self.owner).exists())

    def test_edit_property_post(self):
        response = self.client.post(reverse("edit_property_id", kwargs={"pk": self.property.id}), {
            "name": "Shanti Residency Premium",
            "property_type": "BUILDING",
            "address": "42, 5th Main Road, HSR Layout",
            "city": "Bengaluru",
            "state": "Karnataka",
            "pin_code": "560102",
            "monthly_rent": "14000",
            "security_deposit": "28000",
            "rent_due_day": "5",
            "electricity_rate": "8.50",
        })
        self.assertRedirects(response, reverse("property_detail_id", kwargs={"pk": self.property.id}))
        self.property.refresh_from_db()
        self.assertEqual(self.property.name, "Shanti Residency Premium")

    def test_delete_property_post(self):
        prop_to_delete = Property.objects.create(
            owner=self.owner,
            name="Temporary Lodge",
            property_type="OTHER",
            address="12, Old Road",
            city="Bengaluru",
            state="Karnataka",
            pin_code="560001",
        )
        response = self.client.post(reverse("delete_property", kwargs={"pk": prop_to_delete.id}))
        self.assertRedirects(response, reverse("property_list"))
        self.assertFalse(Property.objects.filter(id=prop_to_delete.id).exists())


class RoomManagementWebViewsTests(WebViewsBaseTestCase):
    def setUp(self):
        super().setUp()
        self.client.login(username="test_owner", password=self.password)

    def test_rooms_list_view(self):
        response = self.client.get(reverse("rooms"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "101")

    def test_add_room_get_and_post(self):
        response = self.client.get(reverse("add_room"))
        self.assertEqual(response.status_code, 200)

        post_response = self.client.post(reverse("add_room"), {
            "property_id": str(self.property.id),
            "room_number": "102",
            "floor_number": "1",
            "room_type": "SINGLE",
            "monthly_rent": "12000",
            "security_deposit": "24000",
        })
        self.assertRedirects(post_response, reverse("rooms"))
        self.assertTrue(Room.objects.filter(property=self.property, room_number="102").exists())

    def test_delete_room_post(self):
        room_to_delete = Room.objects.create(
            property=self.property,
            room_number="999",
            floor="9",
            room_type="SINGLE",
            monthly_rent=Decimal("10000.00"),
            security_deposit=Decimal("20000.00"),
            status="VACANT",
        )
        response = self.client.post(reverse("delete_room", kwargs={"pk": room_to_delete.id}))
        self.assertRedirects(response, reverse("rooms"))
        self.assertFalse(Room.objects.filter(id=room_to_delete.id).exists())


class TenantManagementWebViewsTests(WebViewsBaseTestCase):
    def setUp(self):
        super().setUp()
        self.client.login(username="test_owner", password=self.password)

    def test_tenants_list_view(self):
        response = self.client.get(reverse("tenants"))
        self.assertEqual(response.status_code, 200)

    def test_add_tenant_and_allocate_room(self):
        post_response = self.client.post(reverse("add_tenant"), {
            "full_name": "Aarav Sharma",
            "email": "aarav.sharma@example.com",
            "phone": "+919876543210",
            "emergency_contact": "Sunita Sharma",
            "emergency_phone": "+919829044556",
            "room_id": str(self.room.id),
        })
        self.assertRedirects(post_response, reverse("tenants"))

        tenant = Tenant.objects.get(full_name="Aarav Sharma", owner=self.owner)
        self.assertEqual(tenant.email, "aarav.sharma@example.com")
        self.room.refresh_from_db()
        self.assertEqual(self.room.status, "OCCUPIED")

        # Test Tenant profile view
        profile_res = self.client.get(reverse("tenant_profile_id", kwargs={"pk": tenant.id}))
        self.assertEqual(profile_res.status_code, 200)
        self.assertContains(profile_res, "Aarav Sharma")
        self.assertContains(profile_res, "101")

        # Test Tenant detail edit view
        edit_res = self.client.post(reverse("tenant_detail_id", kwargs={"pk": tenant.id}), {
            "full_name": "Aarav K. Sharma",
            "email": "aarav.new@example.com",
            "phone": "+919876543210",
            "emergency_contact_name": "Sunita Sharma",
            "emergency_contact_phone": "+919829044556",
        })
        self.assertRedirects(edit_res, reverse("tenant_profile_id", kwargs={"pk": tenant.id}))
        tenant.refresh_from_db()
        self.assertEqual(tenant.full_name, "Aarav K. Sharma")
        self.assertEqual(tenant.email, "aarav.new@example.com")


class RentElectricityAndUtilityTests(WebViewsBaseTestCase):
    def setUp(self):
        super().setUp()
        self.client.login(username="test_owner", password=self.password)

        self.tenant = Tenant.objects.create(
            owner=self.owner,
            full_name="Priya Patel",
            email="priya@example.com",
            phone="+919845011223",
        )
        self.agreement = RentalAgreement.objects.create(
            tenant=self.tenant,
            room=self.room,
            start_date=timezone.localdate(),
            monthly_rent=Decimal("12000.00"),
            security_deposit=Decimal("24000.00"),
            status="ACTIVE",
        )
        self.room.status = "OCCUPIED"
        self.room.save(update_fields=["status"])

    def test_rent_management_view(self):
        response = self.client.get(reverse("rent_management"))
        self.assertEqual(response.status_code, 200)

    def test_generate_rent_records(self):
        response = self.client.post(reverse("generate_rent_records"))
        self.assertRedirects(response, reverse("rent_management"))
        self.assertTrue(RentRecord.objects.filter(agreement=self.agreement).exists())

    def test_record_payment(self):
        record = RentRecord.objects.create(
            agreement=self.agreement,
            billing_month=timezone.localdate().replace(day=1),
            rent_amount=Decimal("12000.00"),
            amount_paid=Decimal("0.00"),
            due_date=timezone.localdate().replace(day=10),
            status="PENDING",
        )
        response = self.client.post(reverse("record_payment"), {
            "agreement_id": str(self.agreement.id),
            "amount": "12000.00",
            "payment_type": "RENT",
            "payment_method": "UPI",
            "reference_number": "UPI-TEST-12345",
        })
        self.assertRedirects(response, reverse("rent_management"))
        record.refresh_from_db()
        self.assertEqual(record.status, "PAID")
        self.assertEqual(record.amount_paid, Decimal("12000.00"))

    def test_electricity_flow(self):
        meter = ElectricityMeter.objects.create(
            room=self.room,
            meter_number="MTR-TEST-01",
            installation_date=timezone.localdate(),
            is_active=True,
        )
        # GET form
        res_form = self.client.get(reverse("electricity_bill_form"))
        self.assertEqual(res_form.status_code, 200)
        self.assertContains(res_form, "MTR-TEST-01")

        # POST reading
        res_post = self.client.post(reverse("electricity_bill_form"), {
            "meter_id": str(meter.id),
            "reading_date": str(timezone.localdate()),
            "previous_reading": "100.00",
            "current_reading": "250.00",
            "rate_per_unit": "8.00",
        })
        self.assertRedirects(res_post, reverse("electricity_bill_list"))
        self.assertTrue(ElectricityBill.objects.filter(meter=meter, units_consumed=Decimal("150.00")).exists())

        # GET bills list
        res_list = self.client.get(reverse("electricity_bill_list"))
        self.assertEqual(res_list.status_code, 200)
        self.assertContains(res_list, "MTR-TEST-01")
        self.assertContains(res_list, "150.00 kWh")


class InvoicesReportsNotificationsAndSearchTests(WebViewsBaseTestCase):
    def setUp(self):
        super().setUp()
        self.client.login(username="test_owner", password=self.password)

    def test_invoices_view(self):
        response = self.client.get(reverse("invoice_list"))
        self.assertEqual(response.status_code, 200)

    def test_reports_view(self):
        response = self.client.get(reverse("reports"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Shanti Residency")

    def test_notifications_flow(self):
        tenant = Tenant.objects.create(
            owner=self.owner,
            full_name="Rohan Verma",
            phone="+919876543219",
        )
        agreement = RentalAgreement.objects.create(
            tenant=tenant,
            room=self.room,
            start_date=timezone.localdate(),
            monthly_rent=Decimal("12000.00"),
            status="ACTIVE",
        )
        record = RentRecord.objects.create(
            agreement=agreement,
            billing_month=timezone.localdate().replace(day=1),
            rent_amount=Decimal("12000.00"),
            due_date=timezone.localdate().replace(day=10),
            status="PENDING",
        )
        notif = Notification.objects.create(
            tenant=tenant,
            rent_record=record,
            notification_type="RENT_UPCOMING",
            title="Rent Due Soon",
            message="Your rent is due in 3 days.",
            due_date=record.due_date,
            amount_due=Decimal("12000.00"),
            is_read=False,
        )
        res = self.client.get(reverse("notifications"))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Rent Due Soon")

        # Mark read
        res_read = self.client.get(reverse("mark_notification_read", kwargs={"pk": notif.id}))
        self.assertRedirects(res_read, reverse("notifications"))
        notif.refresh_from_db()
        self.assertTrue(notif.is_read)

    def test_settings_view(self):
        response = self.client.get(reverse("settings"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "test_owner")
        self.assertContains(response, "owner@kirayasaathi.app")

    def test_global_search_endpoint(self):
        response = self.client.get(reverse("global_search") + "?q=Shanti")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(len(data.get("results", [])) > 0)
        self.assertEqual(data["results"][0]["title"], "Shanti Residency")

    def test_unauthenticated_home_view_renders_landing(self):
        self.client.logout()
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "KirayaSaathi")

    def test_authenticated_home_view_redirects_to_dashboard(self):
        self.client.login(username="test_owner", password=self.password)
        response = self.client.get(reverse("home"))
        self.assertRedirects(response, reverse("dashboard"))
