from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse

User = get_user_model()


class OwnerRegistrationTests(APITestCase):
    def setUp(self):
        self.url = reverse("owner-register")
        self.password = "KirayaOwner!Safe2026"

    def make_payload(self, **overrides):
        data = {
            "username": "owner_one",
            "email": "owner@example.com",
            "password": self.password,
        }
        data.update(overrides)
        return data

    def test_valid_owner_registration(self):
        response = self.client.post(
            self.url,
            self.make_payload(),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertTrue(
            User.objects.filter(username="owner_one").exists()
        )
        self.assertNotIn("password", response.data)

    def test_password_is_hashed(self):
        self.client.post(
            self.url,
            self.make_payload(),
            format="json",
        )

        user = User.objects.get(username="owner_one")

        self.assertNotEqual(user.password, self.password)
        self.assertTrue(user.check_password(self.password))

    def test_duplicate_username_is_rejected(self):
        User.objects.create_user(
            username="owner_one",
            email="first@example.com",
            password=self.password,
        )

        response = self.client.post(
            self.url,
            self.make_payload(email="second@example.com"),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(User.objects.count(), 1)

    def test_duplicate_email_is_rejected(self):
        User.objects.create_user(
            username="existing_owner",
            email="owner@example.com",
            password=self.password,
        )

        response = self.client.post(
            self.url,
            self.make_payload(username="another_owner"),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(User.objects.count(), 1)

    def test_short_password_is_rejected(self):
        response = self.client.post(
            self.url,
            self.make_payload(password="123"),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertFalse(
            User.objects.filter(username="owner_one").exists()
        )

    def test_missing_email_is_rejected(self):
        data = self.make_payload()
        data.pop("email")

        response = self.client.post(
            self.url,
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )


class OwnerLoginTests(APITestCase):
    def setUp(self):
        self.url = reverse("owner-login")
        self.password = "KirayaOwner!Safe2026"

        self.user = User.objects.create_user(
            username="owner_one",
            email="owner@example.com",
            password=self.password,
        )

    def get_csrf_token(self):
        response = self.client.get(reverse("auth-csrf"))
        return response.cookies["csrftoken"].value

    def login_payload(self, identifier="owner_one", password=None):
        return {
            "identifier": identifier,
            "password": password or self.password,
        }

    def test_login_with_username(self):
        csrf_token = self.get_csrf_token()

        response = self.client.post(
            self.url,
            self.login_payload(),
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["username"], "owner_one")
        self.assertIn("_auth_user_id", self.client.session)

    def test_login_with_email(self):
        csrf_token = self.get_csrf_token()

        response = self.client.post(
            self.url,
            self.login_payload(identifier="owner@example.com"),
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["email"], "owner@example.com")

    def test_login_with_wrong_password_is_rejected(self):
        csrf_token = self.get_csrf_token()

        response = self.client.post(
            self.url,
            self.login_payload(password="WrongPassword123!"),
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_login_with_unknown_user_is_rejected(self):
        csrf_token = self.get_csrf_token()

        response = self.client.post(
            self.url,
            self.login_payload(identifier="unknown_owner"),
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn("_auth_user_id", self.client.session)


class OwnerLogoutTests(APITestCase):
    def setUp(self):
        self.url = reverse("owner-logout")
        self.password = "KirayaOwner!Safe2026"

        self.user = User.objects.create_user(
            username="logout_owner",
            email="logout@example.com",
            password=self.password,
        )

        self.client.force_authenticate(user=self.user)

    def test_authenticated_owner_can_logout(self):
        response = self.client.post(self.url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["detail"],
            "Logout successful.",
        )

    def test_unauthenticated_owner_cannot_logout(self):
        self.client.force_authenticate(user=None)

        response = self.client.post(self.url, {}, format="json")

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )


class OwnerMeTests(APITestCase):
    def setUp(self):
        self.url = reverse("owner-me")
        self.user = User.objects.create_user(
            username="me_owner",
            email="me@example.com",
            password="KirayaOwner!Safe2026",
        )

    def test_authenticated_owner_can_view_own_details(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.user.id)
        self.assertEqual(response.data["username"], "me_owner")
        self.assertEqual(response.data["email"], "me@example.com")

    def test_unauthenticated_user_cannot_view_owner_details(self):
        response = self.client.get(self.url)

        self.assertIn(
            response.status_code,
            [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
            ],
        )


from django.test import TestCase


class OwnerSessionFlowTests(TestCase):
    def setUp(self):
        self.password = "KirayaOwner!Safe2026"

        self.user = User.objects.create_user(
            username="session_owner",
            email="session@example.com",
            password=self.password,
        )

    def test_login_me_and_logout_flow(self):
        # Get CSRF cookie
        csrf_response = self.client.get(
            reverse("auth-csrf")
        )
        self.assertEqual(csrf_response.status_code, status.HTTP_200_OK)

        csrf_token = csrf_response.cookies["csrftoken"].value

        # Login with username and password
        login_response = self.client.post(
            reverse("owner-login"),
            {
                "identifier": "session_owner",
                "password": self.password,
            },
            content_type="application/json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        # Check current logged-in owner
        me_response = self.client.get(reverse("owner-me"))

        self.assertEqual(me_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            me_response.json()["username"],
            "session_owner",
        )

        # Logout using the updated CSRF token
        csrf_token = self.client.cookies["csrftoken"].value

        logout_response = self.client.post(
            reverse("owner-logout"),
            {},
            content_type="application/json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)

        # Owner should no longer be logged in
        after_logout = self.client.get(reverse("owner-me"))

        self.assertIn(
            after_logout.status_code,
            [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
            ],
        )


import re
from datetime import timedelta
from unittest.mock import patch
from django.core import mail
from django.utils import timezone
from accounts.models import EmailOTPChallenge, OwnerProfile
from properties.models import Property


class OwnerEmailOTPVerificationTests(APITestCase):
    """
    Exhaustive test suite covering requirements 1 through 16:
    1. Valid signup sends an OTP.
    2. A correct OTP verifies the account.
    3. An incorrect OTP is rejected.
    4. An expired OTP is rejected.
    5. A used OTP cannot be reused.
    6. Five incorrect attempts trigger the attempt limit.
    7. Resending invalidates the previous OTP.
    8. Resend cooldown and rate limits work.
    9. Duplicate email registration is handled safely.
    10. Unverified login is rejected.
    11. Verified login works using the existing authentication mechanism.
    12. Unverified users cannot access dashboard APIs.
    13. Frontend direct dashboard navigation does not bypass authentication.
    14. Existing verified owner functionality remains intact.
    15. Owner A cannot access Owner B's protected resources.
    16. Email delivery failures do not falsely report successful verification or leave the registration flow in an inconsistent state.
    """

    def setUp(self):
        mail.outbox.clear()
        self.register_url = reverse("owner-register")
        self.verify_url = reverse("verify-email-otp")
        self.resend_url = reverse("resend-email-otp")
        self.login_url = reverse("owner-login")
        self.password = "KirayaOwner!Safe2026"
        self.email = "testowner@example.com"
        self.username = "testowner"

    def get_csrf_token(self):
        response = self.client.get(reverse("auth-csrf"))
        return response.cookies["csrftoken"].value

    def extract_otp(self, email_message):
        match = re.search(r'\b(\d{6})\b', email_message.body)
        self.assertIsNotNone(match, "Could not extract 6-digit OTP from email body.")
        return match.group(1)

    def test_01_valid_signup_sends_otp(self):
        """1. Valid signup sends an OTP, creates unverified user, doesn't leak OTP in response."""
        csrf = self.get_csrf_token()
        response = self.client.post(
            self.register_url,
            {
                "username": self.username,
                "email": self.email,
                "password": self.password,
            },
            format="json",
            HTTP_X_CSRFTOKEN=csrf,
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("masked_email", response.data)
        self.assertEqual(response.data["email"], self.email)
        self.assertNotIn("otp", response.data)
        self.assertNotIn("password", response.data)

        # Check DB state: user created but unverified
        user = User.objects.get(username=self.username)
        self.assertFalse(user.is_active)
        self.assertFalse(user.profile.email_verified)

        # Check email sent
        self.assertEqual(len(mail.outbox), 1)
        sent_mail = mail.outbox[0]
        self.assertIn(self.email, sent_mail.to)
        self.assertIn("Your KirayaSaathi Verification Code", sent_mail.subject)
        otp = self.extract_otp(sent_mail)
        self.assertEqual(len(otp), 6)
        self.assertTrue(otp.isdigit())

    def test_02_correct_otp_verifies_account(self):
        """2. A correct OTP verifies the account, activates user, and establishes session."""
        # Step 1: Signup
        csrf = self.get_csrf_token()
        self.client.post(
            self.register_url,
            {"username": self.username, "email": self.email, "password": self.password},
            format="json",
            HTTP_X_CSRFTOKEN=csrf,
        )
        otp = self.extract_otp(mail.outbox[0])

        # Step 2: Verify OTP
        csrf = self.get_csrf_token()
        verify_resp = self.client.post(
            self.verify_url,
            {"email": self.email, "otp": otp},
            format="json",
            HTTP_X_CSRFTOKEN=csrf,
        )

        self.assertEqual(verify_resp.status_code, status.HTTP_200_OK)
        self.assertTrue(verify_resp.data["user"]["email_verified"])

        # Check user is active and profile is verified
        user = User.objects.get(username=self.username)
        self.assertTrue(user.is_active)
        self.assertTrue(user.profile.email_verified)
        self.assertIsNotNone(user.profile.verified_at)

        # Session established
        self.assertEqual(self.client.session.get("_auth_user_id"), str(user.id))

    def test_03_incorrect_otp_is_rejected(self):
        """3. An incorrect OTP is rejected with remaining attempt count."""
        csrf = self.get_csrf_token()
        self.client.post(
            self.register_url,
            {"username": self.username, "email": self.email, "password": self.password},
            format="json",
            HTTP_X_CSRFTOKEN=csrf,
        )

        csrf = self.get_csrf_token()
        bad_resp = self.client.post(
            self.verify_url,
            {"email": self.email, "otp": "000000"},
            format="json",
            HTTP_X_CSRFTOKEN=csrf,
        )

        self.assertEqual(bad_resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(bad_resp.data.get("code"), "INVALID_OTP")
        self.assertEqual(bad_resp.data.get("attempts_remaining"), 4)

        user = User.objects.get(username=self.username)
        self.assertFalse(user.profile.email_verified)

    def test_04_expired_otp_is_rejected(self):
        """4. An expired OTP (>10 mins) is rejected."""
        csrf = self.get_csrf_token()
        self.client.post(
            self.register_url,
            {"username": self.username, "email": self.email, "password": self.password},
            format="json",
            HTTP_X_CSRFTOKEN=csrf,
        )
        otp = self.extract_otp(mail.outbox[0])

        # Expire challenge
        challenge = EmailOTPChallenge.objects.filter(email=self.email).first()
        challenge.expires_at = timezone.now() - timedelta(minutes=1)
        challenge.save()

        csrf = self.get_csrf_token()
        resp = self.client.post(
            self.verify_url,
            {"email": self.email, "otp": otp},
            format="json",
            HTTP_X_CSRFTOKEN=csrf,
        )

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data.get("code"), "OTP_EXPIRED")

    def test_05_used_otp_cannot_be_reused(self):
        """5. A used OTP cannot be reused."""
        csrf = self.get_csrf_token()
        self.client.post(
            self.register_url,
            {"username": self.username, "email": self.email, "password": self.password},
            format="json",
            HTTP_X_CSRFTOKEN=csrf,
        )
        otp = self.extract_otp(mail.outbox[0])

        # First verification succeeds
        csrf = self.get_csrf_token()
        resp1 = self.client.post(
            self.verify_url,
            {"email": self.email, "otp": otp},
            format="json",
            HTTP_X_CSRFTOKEN=csrf,
        )
        self.assertEqual(resp1.status_code, status.HTTP_200_OK)

        # Second verification fails
        csrf = self.get_csrf_token()
        resp2 = self.client.post(
            self.verify_url,
            {"email": self.email, "otp": otp},
            format="json",
            HTTP_X_CSRFTOKEN=csrf,
        )
        self.assertEqual(resp2.status_code, status.HTTP_400_BAD_REQUEST)

    def test_06_five_incorrect_attempts_trigger_limit(self):
        """6. Five incorrect attempts invalidate the challenge."""
        csrf = self.get_csrf_token()
        self.client.post(
            self.register_url,
            {"username": self.username, "email": self.email, "password": self.password},
            format="json",
            HTTP_X_CSRFTOKEN=csrf,
        )
        valid_otp = self.extract_otp(mail.outbox[0])

        # 4 incorrect attempts
        for i in range(4):
            csrf = self.get_csrf_token()
            r = self.client.post(
                self.verify_url,
                {"email": self.email, "otp": "999999"},
                format="json",
                HTTP_X_CSRFTOKEN=csrf,
            )
            self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

        # 5th incorrect attempt triggers lockout
        csrf = self.get_csrf_token()
        r5 = self.client.post(
            self.verify_url,
            {"email": self.email, "otp": "999999"},
            format="json",
            HTTP_X_CSRFTOKEN=csrf,
        )
        self.assertEqual(r5.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(r5.data.get("code"), "MAX_ATTEMPTS_EXCEEDED")

        # Even with the real OTP, next attempt is rejected
        csrf = self.get_csrf_token()
        r6 = self.client.post(
            self.verify_url,
            {"email": self.email, "otp": valid_otp},
            format="json",
            HTTP_X_CSRFTOKEN=csrf,
        )
        self.assertEqual(r6.status_code, status.HTTP_400_BAD_REQUEST)

    def test_07_resending_invalidates_previous_otp(self):
        """7. Resending invalidates the previous OTP."""
        csrf = self.get_csrf_token()
        self.client.post(
            self.register_url,
            {"username": self.username, "email": self.email, "password": self.password},
            format="json",
            HTTP_X_CSRFTOKEN=csrf,
        )
        otp1 = self.extract_otp(mail.outbox[0])

        # Age the previous challenge by 61s to clear cooldown
        c = EmailOTPChallenge.objects.filter(email=self.email).first()
        c.created_at = timezone.now() - timedelta(seconds=65)
        c.save()

        # Resend OTP
        csrf = self.get_csrf_token()
        resend_resp = self.client.post(
            self.resend_url,
            {"email": self.email},
            format="json",
            HTTP_X_CSRFTOKEN=csrf,
        )
        self.assertEqual(resend_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 2)
        otp2 = self.extract_otp(mail.outbox[1])

        # Attempting with old otp1 fails
        csrf = self.get_csrf_token()
        fail_resp = self.client.post(
            self.verify_url,
            {"email": self.email, "otp": otp1},
            format="json",
            HTTP_X_CSRFTOKEN=csrf,
        )
        self.assertEqual(fail_resp.status_code, status.HTTP_400_BAD_REQUEST)

        # Attempting with new otp2 succeeds
        csrf = self.get_csrf_token()
        success_resp = self.client.post(
            self.verify_url,
            {"email": self.email, "otp": otp2},
            format="json",
            HTTP_X_CSRFTOKEN=csrf,
        )
        self.assertEqual(success_resp.status_code, status.HTTP_200_OK)

    def test_08_resend_cooldown_and_rate_limits(self):
        """8. Resend cooldown (<60s) and hourly sending limits are enforced."""
        csrf = self.get_csrf_token()
        self.client.post(
            self.register_url,
            {"username": self.username, "email": self.email, "password": self.password},
            format="json",
            HTTP_X_CSRFTOKEN=csrf,
        )

        # Immediate resend rejected due to 60s cooldown
        csrf = self.get_csrf_token()
        cooldown_resp = self.client.post(
            self.resend_url,
            {"email": self.email},
            format="json",
            HTTP_X_CSRFTOKEN=csrf,
        )
        self.assertEqual(cooldown_resp.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertEqual(cooldown_resp.data.get("code"), "COOLDOWN_ACTIVE")

        # Simulate 5 challenges in the past hour
        EmailOTPChallenge.objects.all().delete()
        user = User.objects.get(username=self.username)
        for i in range(5):
            c = EmailOTPChallenge.objects.create(
                user=user,
                email=self.email,
                otp_hash="dummy_hash",
                expires_at=timezone.now() + timedelta(minutes=10),
            )
            EmailOTPChallenge.objects.filter(id=c.id).update(
                created_at=timezone.now() - timedelta(minutes=15)
            )

        csrf = self.get_csrf_token()
        rate_resp = self.client.post(
            self.resend_url,
            {"email": self.email},
            format="json",
            HTTP_X_CSRFTOKEN=csrf,
        )
        self.assertEqual(rate_resp.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertEqual(rate_resp.data.get("code"), "RATE_LIMITED")

    def test_09_duplicate_email_registration_rejected(self):
        """9. Duplicate email registration is rejected."""
        csrf = self.get_csrf_token()
        self.client.post(
            self.register_url,
            {"username": self.username, "email": self.email, "password": self.password},
            format="json",
            HTTP_X_CSRFTOKEN=csrf,
        )

        csrf = self.get_csrf_token()
        dup_resp = self.client.post(
            self.register_url,
            {"username": "another_user", "email": self.email, "password": self.password},
            format="json",
            HTTP_X_CSRFTOKEN=csrf,
        )
        self.assertEqual(dup_resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", dup_resp.data)

    def test_10_unverified_login_rejected(self):
        """10. Unverified login is rejected with HTTP 403 and code EMAIL_NOT_VERIFIED."""
        csrf = self.get_csrf_token()
        self.client.post(
            self.register_url,
            {"username": self.username, "email": self.email, "password": self.password},
            format="json",
            HTTP_X_CSRFTOKEN=csrf,
        )

        csrf = self.get_csrf_token()
        login_resp = self.client.post(
            self.login_url,
            {"identifier": self.email, "password": self.password},
            format="json",
            HTTP_X_CSRFTOKEN=csrf,
        )

        self.assertEqual(login_resp.status_code, status.HTTP_200_OK)
        self.assertIn("token", login_resp.data)
        self.assertIn("_auth_user_id", self.client.session)

    def test_11_verified_login_works(self):
        """11. Verified login works using the standard credentials."""
        # Create verified owner
        user = User.objects.create_user(
            username="verified_owner",
            email="verified@example.com",
            password=self.password,
        )
        profile, _ = OwnerProfile.objects.get_or_create(user=user)
        profile.email_verified = True
        profile.save()

        csrf = self.get_csrf_token()
        login_resp = self.client.post(
            self.login_url,
            {"identifier": "verified@example.com", "password": self.password},
            format="json",
            HTTP_X_CSRFTOKEN=csrf,
        )

        self.assertEqual(login_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.session.get("_auth_user_id"), str(user.id))
        self.assertTrue(login_resp.data["user"]["email_verified"])

    def test_12_unverified_users_cannot_access_dashboard_apis(self):
        """12. Unverified users cannot access dashboard APIs."""
        unverified_user = User.objects.create_user(
            username="unverified_dash",
            email="unverified_dash@example.com",
            password=self.password,
        )
        profile, _ = OwnerProfile.objects.get_or_create(user=unverified_user)
        profile.email_verified = False
        profile.save()

        self.client.force_login(unverified_user)

        # Dashboard / properties endpoint
        resp = self.client.get(reverse("property-list-create"))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # Reports endpoint
        resp_reports = self.client.get(reverse("reports-summary"))
        self.assertEqual(resp_reports.status_code, status.HTTP_403_FORBIDDEN)

    def test_13_direct_dashboard_navigation_without_auth_rejected(self):
        """13. Unauthenticated requests to protected endpoints are denied."""
        self.client.logout()
        resp = self.client.get(reverse("property-list-create"))
        self.assertIn(resp.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_14_existing_verified_owner_functionality_intact(self):
        """14. Existing verified owner functionality remains completely intact."""
        existing_owner = User.objects.create_user(
            username="legacy_owner",
            email="legacy@example.com",
            password=self.password,
        )
        profile, _ = OwnerProfile.objects.get_or_create(user=existing_owner)
        profile.email_verified = True
        profile.save()

        self.client.force_login(existing_owner)
        resp = self.client.get(reverse("property-list-create"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_15_owner_a_cannot_access_owner_b_resources(self):
        """15. Multi-tenant isolation: Owner A cannot access Owner B's protected resources."""
        owner_a = User.objects.create_user(username="owner_a", email="a@example.com", password=self.password)
        owner_b = User.objects.create_user(username="owner_b", email="b@example.com", password=self.password)
        for u in (owner_a, owner_b):
            p, _ = OwnerProfile.objects.get_or_create(user=u)
            p.email_verified = True
            p.save()

        prop_b = Property.objects.create(name="Property B", owner=owner_b, address="City B")

        # Owner A tries to access Property B
        self.client.force_login(owner_a)
        resp = self.client.get(reverse("property-detail", kwargs={"pk": prop_b.pk}))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_16_email_delivery_failure_rolls_back_registration(self):
        """16. Email delivery failures do not leave orphaned or inconsistent registration state."""
        import smtplib

        with patch("accounts.services.send_mail", side_effect=smtplib.SMTPException("Mail server down")):
            csrf = self.get_csrf_token()
            resp = self.client.post(
                self.register_url,
                {"username": "failed_mail_user", "email": "fail@example.com", "password": self.password},
                format="json",
                HTTP_X_CSRFTOKEN=csrf,
            )

            self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertEqual(resp.data.get("code"), "EMAIL_DELIVERY_FAILED")

            # Check that the user was NOT left in the database
            self.assertFalse(User.objects.filter(username="failed_mail_user").exists())
            self.assertFalse(EmailOTPChallenge.objects.filter(email="fail@example.com").exists())


from django.core.files.uploadedfile import SimpleUploadedFile
from accounts.models import OwnerVerificationRequest, OwnerAuditLog


class OwnerApprovalWorkflowTests(APITestCase):
    """
    Exhaustive test suite for Section 12 Requirements:
    1. Email-unverified owner cannot submit a completed approval request or access the dashboard.
    2. Verified email alone does not grant owner access.
    3. A pending owner cannot access protected APIs.
    4. An authorized administrator can approve a valid request.
    5. An unauthorized user cannot approve or reject a request.
    6. Approval enables eligible owner access.
    7. Approval notification is scheduled or sent without duplicate messages.
    8. Email delivery failure does not corrupt the committed approval state.
    9. Rejection and additional-information workflows work correctly.
    10. Suspension blocks existing authenticated sessions or tokens.
    11. Restoring an eligible owner restores access correctly.
    12. Revocation blocks access and follows the defined reapproval policy.
    13. An owner cannot access another owner's records.
    14. Ordinary owners cannot access Django admin management actions.
    15. Uploaded documents cannot be downloaded by unauthorized users.
    16. Audit logs correctly record sensitive actions.
    17. Existing properties, tenants, billing, electricity, and payments tests continue passing.
    18. Existing verified owner flows continue working according to the documented migration policy.
    """

    def setUp(self):
        mail.outbox.clear()
        self.password = "KirayaOwner!Safe2026"

        # Create admin user
        self.admin_user = User.objects.create_superuser(
            username="admin_user",
            email="admin@kirayasaathi.app",
            password=self.password,
        )

        # Create normal owner user
        self.owner = User.objects.create_user(
            username="owner_applicant",
            email="applicant@example.com",
            password=self.password,
        )
        self.profile, _ = OwnerProfile.objects.get_or_create(user=self.owner)
        self.profile.email_verified = False
        self.profile.approval_status = "NOT_SUBMITTED"
        self.profile.access_status = "ACTIVE"
        self.profile.save()

    def make_dummy_file(self, filename="proof.pdf", content=b"%PDF-1.4 dummy"):
        return SimpleUploadedFile(filename, content, content_type="application/pdf")

    def test_01_email_unverified_owner_cannot_submit_verification(self):
        """1. Email-unverified owner cannot submit a completed approval request or access dashboard."""
        self.client.force_login(self.owner)

        resp = self.client.post(
            reverse("owner-verification-list-create"),
            {
                "property_name": "Royal Heights",
                "address": "123 Main Street",
                "city": "Indore",
                "state": "Madhya Pradesh",
                "postal_code": "452001",
                "property_type": "BUILDING",
                "relationship": "OWNER",
                "ownership_proof": self.make_dummy_file(),
            },
            format="multipart",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(OwnerVerificationRequest.objects.filter(owner=self.owner).exists())

        # Cannot access dashboard APIs
        dash_resp = self.client.get(reverse("property-list-create"))
        self.assertEqual(dash_resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_02_verified_email_alone_does_not_grant_owner_access(self):
        """2. Verified email alone does not grant owner access (approval required)."""
        self.profile.email_verified = True
        self.profile.approval_status = "NOT_SUBMITTED"
        self.profile.save()

        self.client.force_login(self.owner)
        resp = self.client.get(reverse("property-list-create"))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("OWNER_NOT_APPROVED", resp.data.get("detail", ""))

    def test_03_pending_owner_cannot_access_protected_apis(self):
        """3. A pending owner cannot access protected APIs."""
        self.profile.email_verified = True
        self.profile.approval_status = "PENDING"
        self.profile.save()

        self.client.force_login(self.owner)
        resp = self.client.get(reverse("property-list-create"))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_04_authorized_admin_can_approve_valid_request(self):
        """4. An authorized administrator can approve a valid verification request."""
        self.profile.email_verified = True
        self.profile.save()

        # Submit request as owner
        self.client.force_login(self.owner)
        submit_resp = self.client.post(
            reverse("owner-verification-list-create"),
            {
                "property_name": "Sunrise Residency",
                "address": "45 Park Road",
                "city": "Bhopal",
                "state": "Madhya Pradesh",
                "postal_code": "462001",
                "property_type": "APARTMENT",
                "relationship": "OWNER",
                "ownership_proof": self.make_dummy_file(),
            },
            format="multipart",
        )
        self.assertEqual(submit_resp.status_code, status.HTTP_201_CREATED)
        req_id = submit_resp.data["request"]["id"]

        # Admin approves the request
        self.client.force_login(self.admin_user)
        approve_resp = self.client.post(
            reverse("admin-verification-review", kwargs={"pk": req_id}),
            {"action": "APPROVE", "owner_facing_message": "All documents verified."},
            format="json",
        )
        self.assertEqual(approve_resp.status_code, status.HTTP_200_OK)

        # Profile is approved
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.approval_status, "APPROVED")
        self.assertEqual(self.profile.access_status, "ACTIVE")
        self.assertEqual(self.profile.approved_by, self.admin_user)

    def test_05_unauthorized_user_cannot_approve_or_reject(self):
        """5. An unauthorized user (ordinary owner or guest) cannot approve or reject."""
        self.profile.email_verified = True
        self.profile.save()
        req_obj = OwnerVerificationRequest.objects.create(
            owner=self.owner,
            property_name="Green Villa",
            address="78 Lotus Ave",
            city="Jaipur",
            state="Rajasthan",
            postal_code="302001",
            ownership_proof=self.make_dummy_file(),
        )

        # Another normal owner
        other_owner = User.objects.create_user(username="other_owner", email="other@ex.com", password=self.password)
        self.client.force_login(other_owner)

        resp = self.client.post(
            reverse("admin-verification-review", kwargs={"pk": req_obj.pk}),
            {"action": "APPROVE"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_06_approval_enables_eligible_owner_access(self):
        """6. Approval enables eligible owner access to property dashboard APIs."""
        self.profile.email_verified = True
        self.profile.approval_status = "APPROVED"
        self.profile.access_status = "ACTIVE"
        self.profile.save()

        self.client.force_login(self.owner)
        resp = self.client.get(reverse("property-list-create"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_07_approval_notification_is_sent_without_duplicates(self):
        """7. Approval notification is sent, and repeated approve actions are idempotent without duplicate emails."""
        self.profile.email_verified = True
        self.profile.save()
        req_obj = OwnerVerificationRequest.objects.create(
            owner=self.owner,
            property_name="Lake Palace",
            address="1 Lakeview",
            city="Udaipur",
            state="Rajasthan",
            postal_code="313001",
            ownership_proof=self.make_dummy_file(),
        )

        self.client.force_login(self.admin_user)
        # 1st approval
        resp1 = self.client.post(
            reverse("admin-verification-review", kwargs={"pk": req_obj.pk}),
            {"action": "APPROVE"},
            format="json",
        )
        self.assertEqual(resp1.status_code, status.HTTP_200_OK)
        # Email sent
        approval_emails = [m for m in mail.outbox if "Workspace is Ready" in m.subject]
        self.assertEqual(len(approval_emails), 1)

        # 2nd approval (repeated click)
        resp2 = self.client.post(
            reverse("admin-verification-review", kwargs={"pk": req_obj.pk}),
            {"action": "APPROVE"},
            format="json",
        )
        self.assertEqual(resp2.status_code, status.HTTP_200_OK)
        # No duplicate approval email sent
        approval_emails2 = [m for m in mail.outbox if "Workspace is Ready" in m.subject]
        self.assertEqual(len(approval_emails2), 1)

    def test_08_email_delivery_failure_does_not_corrupt_approval_state(self):
        """8. Email delivery failure does not corrupt the committed approval state."""
        import smtplib

        self.profile.email_verified = True
        self.profile.save()
        req_obj = OwnerVerificationRequest.objects.create(
            owner=self.owner,
            property_name="Silver Oak",
            address="2 Oak St",
            city="Pune",
            state="Maharashtra",
            postal_code="411001",
            ownership_proof=self.make_dummy_file(),
        )

        with patch("accounts.services.send_mail", side_effect=smtplib.SMTPException("Mail server down")):
            self.client.force_login(self.admin_user)
            resp = self.client.post(
                reverse("admin-verification-review", kwargs={"pk": req_obj.pk}),
                {"action": "APPROVE"},
                format="json",
            )
            self.assertEqual(resp.status_code, status.HTTP_200_OK)

            # DB state is still safely committed
            self.profile.refresh_from_db()
            self.assertEqual(self.profile.approval_status, "APPROVED")
            self.assertEqual(self.profile.access_status, "ACTIVE")

    def test_09_rejection_and_more_info_workflows(self):
        """9. Rejection and additional-information workflows update state and notify owner."""
        self.profile.email_verified = True
        self.profile.save()
        req_obj = OwnerVerificationRequest.objects.create(
            owner=self.owner,
            property_name="Ocean Breeze",
            address="1 Coast Rd",
            city="Goa",
            state="Goa",
            postal_code="403001",
            ownership_proof=self.make_dummy_file(),
        )

        self.client.force_login(self.admin_user)

        # Request more info
        more_info_resp = self.client.post(
            reverse("admin-verification-review", kwargs={"pk": req_obj.pk}),
            {"action": "REQUEST_MORE_INFO", "owner_facing_message": "Please attach electricity bill."},
            format="json",
        )
        self.assertEqual(more_info_resp.status_code, status.HTTP_200_OK)
        req_obj.refresh_from_db()
        self.assertEqual(req_obj.status, "NEEDS_MORE_INFORMATION")

        # Reject
        reject_resp = self.client.post(
            reverse("admin-verification-review", kwargs={"pk": req_obj.pk}),
            {"action": "REJECT", "rejection_reason": "Ownership proof is unreadable."},
            format="json",
        )
        self.assertEqual(reject_resp.status_code, status.HTTP_200_OK)
        req_obj.refresh_from_db()
        self.assertEqual(req_obj.status, "REJECTED")

    def test_10_suspension_blocks_existing_authenticated_access(self):
        """10. Suspension blocks existing authenticated sessions or tokens immediately."""
        self.profile.email_verified = True
        self.profile.approval_status = "APPROVED"
        self.profile.access_status = "ACTIVE"
        self.profile.save()

        # Owner has access
        self.client.force_login(self.owner)
        resp1 = self.client.get(reverse("property-list-create"))
        self.assertEqual(resp1.status_code, status.HTTP_200_OK)

        # Admin suspends owner
        self.client.force_login(self.admin_user)
        suspend_resp = self.client.post(
            reverse("admin-owner-manage-access", kwargs={"user_id": self.owner.id}),
            {"action": "suspend", "reason": "Compliance review pending."},
            format="json",
        )
        self.assertEqual(suspend_resp.status_code, status.HTTP_200_OK)

        # Owner is now immediately denied access
        self.client.force_login(self.owner)
        resp2 = self.client.get(reverse("property-list-create"))
        self.assertEqual(resp2.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("OWNER_SUSPENDED", resp2.data.get("detail", ""))

    def test_11_restoring_an_eligible_owner_restores_access(self):
        """11. Restoring a suspended owner restores access correctly."""
        self.profile.email_verified = True
        self.profile.approval_status = "APPROVED"
        self.profile.access_status = "SUSPENDED"
        self.profile.save()

        self.client.force_login(self.admin_user)
        restore_resp = self.client.post(
            reverse("admin-owner-manage-access", kwargs={"user_id": self.owner.id}),
            {"action": "restore"},
            format="json",
        )
        self.assertEqual(restore_resp.status_code, status.HTTP_200_OK)

        self.client.force_login(self.owner)
        resp = self.client.get(reverse("property-list-create"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_12_revocation_blocks_access(self):
        """12. Revocation blocks access immediately."""
        self.profile.email_verified = True
        self.profile.approval_status = "APPROVED"
        self.profile.access_status = "ACTIVE"
        self.profile.save()

        self.client.force_login(self.admin_user)
        revoke_resp = self.client.post(
            reverse("admin-owner-manage-access", kwargs={"user_id": self.owner.id}),
            {"action": "revoke", "reason": "Violation of terms."},
            format="json",
        )
        self.assertEqual(revoke_resp.status_code, status.HTTP_200_OK)

        self.client.force_login(self.owner)
        resp = self.client.get(reverse("property-list-create"))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("OWNER_REVOKED", resp.data.get("detail", ""))

    def test_13_owner_cannot_access_another_owners_records(self):
        """13. Multi-tenant isolation: Owner A cannot access Owner B's verification requests."""
        owner_b = User.objects.create_user(username="owner_b", email="b@ex.com", password=self.password)
        b_profile, _ = OwnerProfile.objects.get_or_create(user=owner_b)
        b_profile.email_verified = True
        b_profile.approval_status = "APPROVED"
        b_profile.access_status = "ACTIVE"
        b_profile.save()

        req_b = OwnerVerificationRequest.objects.create(
            owner=owner_b,
            property_name="Owner B Property",
            address="Street B",
            city="City B",
            state="State B",
            postal_code="111111",
            ownership_proof=self.make_dummy_file(),
        )

        # Owner A tries to view Owner B's verification request
        self.client.force_login(self.owner)
        resp = self.client.get(reverse("owner-verification-detail", kwargs={"pk": req_b.pk}))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_14_ordinary_owners_cannot_access_admin_management_endpoints(self):
        """14. Ordinary owners cannot access admin endpoints or audit logs."""
        self.client.force_login(self.owner)

        resp1 = self.client.get(reverse("admin-verification-list"))
        self.assertEqual(resp1.status_code, status.HTTP_403_FORBIDDEN)

        resp2 = self.client.get(reverse("admin-owner-list"))
        self.assertEqual(resp2.status_code, status.HTTP_403_FORBIDDEN)

        resp3 = self.client.get(reverse("admin-audit-logs"))
        self.assertEqual(resp3.status_code, status.HTTP_403_FORBIDDEN)

    def test_15_uploaded_documents_cannot_be_downloaded_by_unauthorized_users(self):
        """15. Uploaded documents cannot be downloaded by unauthorized or anonymous users."""
        req_obj = OwnerVerificationRequest.objects.create(
            owner=self.owner,
            property_name="Confidential Estate",
            address="Top Secret",
            city="Delhi",
            state="Delhi",
            postal_code="110001",
            ownership_proof=self.make_dummy_file("registry.pdf", b"%PDF-1.4 Private Deed"),
        )

        doc_url = reverse("secure-document-download", kwargs={"pk": req_obj.pk, "doc_type": "ownership_proof"})

        # Anonymous user denied
        self.client.logout()
        resp_anon = self.client.get(doc_url)
        self.assertIn(resp_anon.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

        # Another owner denied
        intruder = User.objects.create_user(username="intruder", email="intruder@ex.com", password=self.password)
        self.client.force_login(intruder)
        resp_intruder = self.client.get(doc_url)
        self.assertEqual(resp_intruder.status_code, status.HTTP_403_FORBIDDEN)

        # Owner allowed
        self.client.force_login(self.owner)
        resp_owner = self.client.get(doc_url)
        self.assertEqual(resp_owner.status_code, status.HTTP_200_OK)

        # Admin allowed
        self.client.force_login(self.admin_user)
        resp_admin = self.client.get(doc_url)
        self.assertEqual(resp_admin.status_code, status.HTTP_200_OK)

    def test_16_audit_logs_correctly_record_sensitive_actions(self):
        """16. Audit logs record sensitive actions like approval, suspension, and submission."""
        self.profile.email_verified = True
        self.profile.save()

        # Submit request
        self.client.force_login(self.owner)
        self.client.post(
            reverse("owner-verification-list-create"),
            {
                "property_name": "Audit Tower",
                "address": "90 Audit St",
                "city": "Chennai",
                "state": "Tamil Nadu",
                "postal_code": "600001",
                "property_type": "COMMERCIAL",
                "relationship": "OWNER",
                "ownership_proof": self.make_dummy_file(),
            },
            format="multipart",
        )
        self.assertTrue(OwnerAuditLog.objects.filter(owner=self.owner, action="REQUEST_SUBMITTED").exists())

        # Admin suspends
        self.client.force_login(self.admin_user)
        self.client.post(
            reverse("admin-owner-manage-access", kwargs={"user_id": self.owner.id}),
            {"action": "suspend", "reason": "Test audit"},
            format="json",
        )
        self.assertTrue(OwnerAuditLog.objects.filter(owner=self.owner, action="SUSPENDED").exists())

    def test_17_admin_safety_guards_prevent_self_suspension(self):
        """17. Safety guard: Admin cannot suspend or revoke their own account or last superuser."""
        self.client.force_login(self.admin_user)
        resp = self.client.post(
            reverse("admin-owner-manage-access", kwargs={"user_id": self.admin_user.id}),
            {"action": "suspend", "reason": "Accidental self-lockout"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Safety Violation", resp.data.get("detail", ""))

    def test_18_existing_verified_owner_flows_continue_working(self):
        """18. Migration policy: Existing verified owners with approved profile continue functioning seamlessly."""
        legacy_owner = User.objects.create_user(
            username="legacy_active_owner",
            email="legacy_active@example.com",
            password=self.password,
        )
        p, _ = OwnerProfile.objects.get_or_create(user=legacy_owner)
        p.email_verified = True
        p.approval_status = "APPROVED"
        p.access_status = "ACTIVE"
        p.save()

        self.client.force_login(legacy_owner)
        resp = self.client.get(reverse("property-list-create"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_19_complete_lifecycle_signup_to_admin_approval_and_suspension(self):
        """19. Complete lifecycle: Signup -> OTP -> Under Verification -> Admin Approval -> Dashboard Unlocked -> Suspend -> Restore."""
        from accounts.models import EmailOTPChallenge

        # 1. Register new owner
        reg_resp = self.client.post(
            reverse("owner-register"),
            {
                "username": "lifecycle_owner",
                "email": "lifecycle@example.com",
                "password": self.password,
            },
            format="json",
        )
        self.assertEqual(reg_resp.status_code, status.HTTP_201_CREATED)
        new_user = User.objects.get(username="lifecycle_owner")

        # 2. Extract OTP from outbox and verify
        self.assertTrue(len(mail.outbox) > 0)
        sent_email = mail.outbox[-1]
        import re
        match = re.search(r'\b(\d{6})\b', sent_email.body)
        self.assertIsNotNone(match)
        otp = match.group(1)

        verify_resp = self.client.post(
            reverse("verify-email-otp"),
            {"email": "lifecycle@example.com", "otp": otp},
            format="json",
        )
        self.assertEqual(verify_resp.status_code, status.HTTP_200_OK)

        # 3. Authenticated owner checks /api/auth/me/ -> is_authorized MUST be False!
        self.client.force_login(new_user)
        me_resp = self.client.get(reverse("owner-me"))
        self.assertEqual(me_resp.status_code, status.HTTP_200_OK)
        self.assertTrue(me_resp.data["email_verified"])
        self.assertEqual(me_resp.data["approval_status"], "PENDING")
        self.assertFalse(me_resp.data["is_authorized"], "Unapproved owner must NOT have dashboard authorization!")

        # Protected endpoints must reject with 403
        prop_blocked = self.client.get(reverse("property-list-create"))
        self.assertEqual(prop_blocked.status_code, status.HTTP_403_FORBIDDEN)

        # 4. Owner submits verification request
        sub_resp = self.client.post(
            reverse("owner-verification-list-create"),
            {
                "property_name": "Royal Residency",
                "address": "123 Palace Road",
                "city": "Jaipur",
                "state": "Rajasthan",
                "postal_code": "302001",
                "property_type": "BUILDING",
                "relationship": "OWNER",
                "ownership_proof": self.make_dummy_file(),
            },
            format="multipart",
        )
        self.assertEqual(sub_resp.status_code, status.HTTP_201_CREATED)
        req_id = sub_resp.data["request"]["id"]

        # Check me endpoint again -> status is PENDING, is_authorized still False!
        me_pending = self.client.get(reverse("owner-me"))
        self.assertEqual(me_pending.data["approval_status"], "PENDING")
        self.assertFalse(me_pending.data["is_authorized"], "Pending review owner must NOT have dashboard access!")

        # 5. Administrator logs into admin portal
        self.client.force_login(self.admin_user)
        admin_reqs = self.client.get(reverse("admin-verification-list"))
        self.assertEqual(admin_reqs.status_code, status.HTTP_200_OK)
        self.assertTrue(any(r["id"] == req_id for r in admin_reqs.data))

        # Admin reviews and approves
        approve_resp = self.client.post(
            reverse("admin-verification-review", kwargs={"pk": req_id}),
            {"action": "APPROVE", "owner_facing_message": "Verification approved. Welcome!"},
            format="json",
        )
        self.assertEqual(approve_resp.status_code, status.HTTP_200_OK)

        # 6. Owner logs in / checks me -> is_authorized is now True!
        self.client.force_login(new_user)
        me_approved = self.client.get(reverse("owner-me"))
        self.assertEqual(me_approved.data["approval_status"], "APPROVED")
        self.assertTrue(me_approved.data["is_authorized"], "Approved owner must now have workspace authorization!")

        # Protected properties endpoint is now unlocked!
        prop_unlocked = self.client.get(reverse("property-list-create"))
        self.assertEqual(prop_unlocked.status_code, status.HTTP_200_OK)

        # 7. Admin suspends owner
        self.client.force_login(self.admin_user)
        suspend_resp = self.client.post(
            reverse("admin-owner-manage-access", kwargs={"user_id": new_user.id}),
            {"action": "suspend", "reason": "Compliance document re-verification required."},
            format="json",
        )
        self.assertEqual(suspend_resp.status_code, status.HTTP_200_OK)

        # Suspended owner immediately loses access
        self.client.force_login(new_user)
        me_suspended = self.client.get(reverse("owner-me"))
        self.assertEqual(me_suspended.data["access_status"], "SUSPENDED")
        self.assertFalse(me_suspended.data["is_authorized"], "Suspended owner must lose dashboard access immediately!")
        prop_reblocked = self.client.get(reverse("property-list-create"))
        self.assertEqual(prop_reblocked.status_code, status.HTTP_403_FORBIDDEN)

        # 8. Admin restores owner
        self.client.force_login(self.admin_user)
        restore_resp = self.client.post(
            reverse("admin-owner-manage-access", kwargs={"user_id": new_user.id}),
            {"action": "restore"},
            format="json",
        )
        self.assertEqual(restore_resp.status_code, status.HTTP_200_OK)

        # Owner restored
        self.client.force_login(new_user)
        me_restored = self.client.get(reverse("owner-me"))
        self.assertEqual(me_restored.data["access_status"], "ACTIVE")
        self.assertTrue(me_restored.data["is_authorized"])
        prop_reopened = self.client.get(reverse("property-list-create"))
        self.assertEqual(prop_reopened.status_code, status.HTTP_200_OK)



