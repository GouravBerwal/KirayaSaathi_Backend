import os
import uuid
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

User = get_user_model()

APPROVAL_STATUS_CHOICES = [
    ("NOT_SUBMITTED", "Not Submitted"),
    ("PENDING", "Pending Review"),
    ("APPROVED", "Approved"),
    ("REJECTED", "Rejected"),
    ("NEEDS_MORE_INFORMATION", "Needs More Information"),
]

ACCESS_STATUS_CHOICES = [
    ("ACTIVE", "Active"),
    ("SUSPENDED", "Suspended"),
    ("REVOKED", "Revoked"),
]

RELATIONSHIP_CHOICES = [
    ("OWNER", "Property Owner"),
    ("AUTHORIZED_MANAGER", "Authorized Manager / Caretaker"),
    ("LEASE_HOLDER", "Lease Holder"),
    ("OTHER", "Other"),
]

PROPERTY_TYPE_CHOICES = [
    ("BUILDING", "Building / Residential Complex"),
    ("HOSTEL", "Hostel"),
    ("PG", "PG / Co-Living"),
    ("APARTMENT", "Apartment / Flat"),
    ("HOUSE", "Independent House / Villa"),
    ("COMMERCIAL", "Commercial Property"),
    ("OTHER", "Other"),
]


def secure_verification_upload_to(instance, filename):
    """
    Generate unique, non-guessable storage path in private media directory.
    Prevents path traversal and directory enumeration.
    """
    ext = os.path.splitext(filename)[1].lower()
    safe_name = f"{uuid.uuid4().hex}{ext}"
    return os.path.join("verification_documents", safe_name)


class OwnerProfile(models.Model):
    """
    Stores owner verification, approval status, and lifecycle access controls.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    email_verified = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Designates whether the owner has verified their email via OTP.",
    )
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when the owner completed email OTP verification.",
    )

    # Admin approval workflow
    approval_status = models.CharField(
        max_length=30,
        choices=APPROVAL_STATUS_CHOICES,
        default="NOT_SUBMITTED",
        db_index=True,
        help_text="Current state of property ownership verification and admin approval.",
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when administrator approved this owner.",
    )
    approved_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="approved_profiles",
        help_text="Administrator who approved this owner.",
    )
    owner_facing_message = models.TextField(
        blank=True,
        default="",
        help_text="Message displayed to the owner regarding approval or information request.",
    )
    internal_notes = models.TextField(
        blank=True,
        default="",
        help_text="Private administrative notes not visible to owner.",
    )

    # Access management (Suspend / Revoke / Restore)
    access_status = models.CharField(
        max_length=20,
        choices=ACCESS_STATUS_CHOICES,
        default="ACTIVE",
        db_index=True,
        help_text="Current operational access state of the owner account.",
    )
    suspension_reason = models.TextField(
        blank=True,
        default="",
        help_text="Reason recorded when owner access is suspended.",
    )
    suspended_at = models.DateTimeField(null=True, blank=True)
    revocation_reason = models.TextField(
        blank=True,
        default="",
        help_text="Reason recorded when owner authorization is revoked.",
    )
    revoked_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Owner Profile"
        verbose_name_plural = "Owner Profiles"

    def __str__(self):
        return f"{self.user.username} (Email: {'Verified' if self.email_verified else 'Unverified'} | Approval: {self.approval_status} | Access: {self.access_status})"

    def is_owner_authorized(self) -> bool:
        """
        True only if owner has verified their email, has admin approval, and account is active.
        """
        return (
            self.email_verified
            and self.approval_status == "APPROVED"
            and self.access_status == "ACTIVE"
        )


class EmailOTPChallenge(models.Model):
    """
    Stores cryptographically hashed, single-use email verification OTP challenges.
    Plaintext OTP is never stored in the database.
    """
    email = models.EmailField(db_index=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="otp_challenges",
        null=True,
        blank=True,
    )
    otp_hash = models.CharField(
        max_length=128,
        help_text="Keyed HMAC-SHA256 hash of the OTP.",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    expires_at = models.DateTimeField(db_index=True)
    attempts = models.PositiveIntegerField(
        default=0,
        help_text="Count of incorrect verification attempts.",
    )
    max_attempts = models.PositiveIntegerField(
        default=5,
        help_text="Maximum allowed incorrect attempts before challenge invalidation.",
    )
    is_consumed = models.BooleanField(
        default=False,
        db_index=True,
        help_text="True if this OTP has already been verified or invalidated.",
    )
    consumed_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        verbose_name = "Email OTP Challenge"
        verbose_name_plural = "Email OTP Challenges"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["email", "is_consumed", "-created_at"]),
        ]

    def __str__(self):
        status = "Consumed" if self.is_consumed else ("Expired" if self.is_expired() else "Active")
        return f"OTP for {self.email} [{status}] ({self.attempts}/{self.max_attempts})"

    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    def has_exceeded_attempts(self) -> bool:
        return self.attempts >= self.max_attempts

    def is_valid_challenge(self) -> bool:
        return not self.is_consumed and not self.is_expired() and not self.has_exceeded_attempts()


class OwnerVerificationRequest(models.Model):
    """
    Property ownership verification request submitted by an email-verified owner.
    Reviewed by administrators before granting dashboard access.
    """
    STATUS_CHOICES = [
        ("PENDING", "Pending Review"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
        ("NEEDS_MORE_INFORMATION", "Needs More Information"),
    ]

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="verification_requests",
    )
    property_name = models.CharField(
        max_length=255,
        help_text="Name of the rental property (e.g. Sunrise Residency)",
    )
    address = models.TextField(
        help_text="Complete physical address of the property",
    )
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    property_type = models.CharField(
        max_length=50,
        choices=PROPERTY_TYPE_CHOICES,
        default="BUILDING",
    )
    relationship = models.CharField(
        max_length=50,
        choices=RELATIONSHIP_CHOICES,
        default="OWNER",
        help_text="Applicant relationship to this property",
    )

    # Uploaded verification proof files (Stored securely in private storage)
    ownership_proof = models.FileField(
        upload_to=secure_verification_upload_to,
        null=True,
        blank=True,
        help_text="Primary proof: Sale deed, registered agreement, property tax receipt",
    )
    utility_bill = models.FileField(
        upload_to=secure_verification_upload_to,
        null=True,
        blank=True,
        help_text="Optional: Electricity, water, or municipal utility bill",
    )
    authorization_letter = models.FileField(
        upload_to=secure_verification_upload_to,
        null=True,
        blank=True,
        help_text="Optional: Power of attorney or manager authorization letter",
    )
    notes = models.TextField(
        blank=True,
        default="",
        help_text="Optional notes or remarks from applicant",
    )

    # Review status and admin decisions
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="PENDING",
        db_index=True,
    )
    submitted_at = models.DateTimeField(auto_now_add=True, db_index=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_verification_requests",
    )
    owner_facing_message = models.TextField(
        blank=True,
        default="",
        help_text="Explanatory feedback message sent to owner",
    )
    internal_notes = models.TextField(
        blank=True,
        default="",
        help_text="Private administrative review notes",
    )
    rejection_reason = models.TextField(
        blank=True,
        default="",
        help_text="Recorded reason if application was rejected",
    )

    class Meta:
        verbose_name = "Owner Verification Request"
        verbose_name_plural = "Owner Verification Requests"
        ordering = ["-submitted_at"]
        indexes = [
            models.Index(fields=["owner", "status", "-submitted_at"]),
        ]

    def __str__(self):
        return f"Request #{self.id} by {self.owner.username} ({self.property_name}) [{self.status}]"


class OwnerAuditLog(models.Model):
    """
    Immutable audit log for sensitive administrator and owner lifecycle actions.
    """
    ACTION_CHOICES = [
        ("REQUEST_SUBMITTED", "Verification Request Submitted"),
        ("APPROVED", "Owner Approved"),
        ("REJECTED", "Owner Rejected"),
        ("MORE_INFO_REQUESTED", "More Information Requested"),
        ("SUSPENDED", "Owner Suspended"),
        ("RESTORED", "Owner Restored"),
        ("REVOKED", "Owner Revoked"),
        ("NOTE_ADDED", "Admin Note Added"),
    ]

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="audit_logs",
    )
    performed_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="performed_audit_logs",
    )
    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES,
        db_index=True,
    )
    notes = models.TextField(blank=True, default="")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Owner Audit Log"
        verbose_name_plural = "Owner Audit Logs"
        ordering = ["-created_at"]

    def __str__(self):
        actor = self.performed_by.username if self.performed_by else "System"
        return f"[{self.created_at:%Y-%m-%d %H:%M}] {self.action} on {self.owner.username} by {actor}"
