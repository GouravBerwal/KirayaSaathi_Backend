from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from accounts.models import OwnerProfile, OwnerVerificationRequest

User = get_user_model()

class Command(BaseCommand):
    help = "Creates or updates an admin/owner account with full dashboard access and verified status."

    def add_arguments(self, parser):
        parser.add_argument("--username", type=str, default="gouravberwal003", help="Username")
        parser.add_argument("--email", type=str, default="gouravberwal003@gmail.com", help="Email address")
        parser.add_argument("--password", type=str, default="KirayaSaathi#2026", help="Password")
        parser.add_argument("--first_name", type=str, default="Gourav", help="First name")
        parser.add_argument("--last_name", type=str, default="Berwal", help="Last name")

    def handle(self, *args, **options):
        username = options["username"].strip()
        email = options["email"].strip().lower()
        password = options["password"]
        first_name = options["first_name"]
        last_name = options["last_name"]

        # Check if user exists by username or email
        user = User.objects.filter(username__iexact=username).first()
        if not user:
            user = User.objects.filter(email__iexact=email).first()

        if user:
            user.username = username
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.is_active = True
            user.is_staff = True
            user.is_superuser = True
            user.set_password(password)
            user.save()
            action = "Updated"
        else:
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )
            action = "Created"

        # Update or create OwnerProfile with full authorization
        profile, _ = OwnerProfile.objects.get_or_create(user=user)
        profile.email_verified = True
        profile.verified_at = timezone.now()
        profile.approval_status = "APPROVED"
        profile.access_status = "ACTIVE"
        profile.owner_facing_message = "Your KirayaSaathi workspace is active and approved."
        profile.save()

        # Update or create OwnerVerificationRequest so admin portal recognizes it as approved
        ver_req, _ = OwnerVerificationRequest.objects.get_or_create(
            owner=user,
            defaults={
                "property_name": f"{username}'s Property",
                "address": "KirayaSaathi Head Office",
                "city": "Indore",
                "state": "Madhya Pradesh",
                "postal_code": "452001",
                "property_type": "BUILDING",
                "relationship": "OWNER",
                "status": "APPROVED",
                "notes": "Admin superuser account automatically verified.",
            }
        )
        ver_req.status = "APPROVED"
        ver_req.reviewed_at = timezone.now()
        ver_req.reviewed_by = user
        ver_req.save()

        self.stdout.write(self.style.SUCCESS(
            f"\n============================================================\n"
            f"🎉 {action} Admin / Owner Account Successfully!\n"
            f"============================================================\n"
            f"Username: {username}\n"
            f"Email:    {email}\n"
            f"Password: {password}\n"
            f"Status:   APPROVED & SUPERUSER (Full Dashboard Access)\n"
            f"============================================================\n"
        ))
