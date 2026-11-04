from django.contrib.auth import authenticate, get_user_model, password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import models, transaction
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.exceptions import APIException

from .models import OwnerProfile
from .services import issue_otp_challenge, mask_email

User = get_user_model()


class UnverifiedEmailError(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_code = "EMAIL_NOT_VERIFIED"
    default_detail = "Your email address is not verified. Please verify your email via OTP."

    def __init__(self, email):
        self.detail = {
            "detail": self.default_detail,
            "code": self.default_code,
            "email": email,
            "masked_email": mask_email(email),
        }


class OwnerRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        trim_whitespace=False,
        style={"input_type": "password"},
    )
    confirm_password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        trim_whitespace=False,
        style={"input_type": "password"},
    )
    first_name = serializers.CharField(required=False, allow_blank=True, default="")
    last_name = serializers.CharField(required=False, allow_blank=True, default="")

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "password",
            "confirm_password",
            "first_name",
            "last_name",
        ]
        read_only_fields = ["id"]
        extra_kwargs = {
            "email": {"required": True},
            "username": {"required": True},
        }

    def validate_username(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Username is required.")

        existing = User.objects.filter(username__iexact=value).first()
        if existing and getattr(getattr(existing, "profile", None), "email_verified", False):
            raise serializers.ValidationError(
                "This username is already registered."
            )
        return value

    def validate_email(self, value):
        value = value.strip().lower()
        if not value:
            raise serializers.ValidationError("Email is required.")

        existing = User.objects.filter(email__iexact=value).first()
        if existing and getattr(getattr(existing, "profile", None), "email_verified", False):
            raise serializers.ValidationError(
                "This email is already registered."
            )
        return value

    def validate(self, attrs):
        password = attrs.get("password")
        confirm_password = attrs.get("confirm_password")

        if confirm_password and password != confirm_password:
            raise serializers.ValidationError(
                {"confirm_password": ["Passwords do not match."]}
            )

        try:
            password_validation.validate_password(password)
        except DjangoValidationError as error:
            raise serializers.ValidationError(
                {"password": list(error.messages)}
            )

        return attrs

    def create(self, validated_data):
        validated_data.pop("confirm_password", None)
        first_name = validated_data.pop("first_name", "")
        last_name = validated_data.pop("last_name", "")

        with transaction.atomic():
            # If an unverified user exists with the same username or email, clean up to allow clean re-registration
            stale_users = User.objects.filter(
                models.Q(email__iexact=validated_data["email"].strip()) |
                models.Q(username__iexact=validated_data["username"].strip())
            )
            for stale in stale_users:
                if not getattr(getattr(stale, "profile", None), "email_verified", False):
                    stale.delete()

            user = User(
                username=validated_data["username"],
                email=validated_data["email"].strip().lower(),
                first_name=first_name,
                last_name=last_name,
                is_active=False,  # Unverified until OTP verification
            )
            user.set_password(validated_data["password"])
            user._default_verified = False
            user._default_approval = "NOT_SUBMITTED"
            user._default_access = "ACTIVE"
            user.save()

            # Explicitly mark profile as unverified and not submitted
            profile, _ = OwnerProfile.objects.get_or_create(user=user)
            profile.email_verified = False
            profile.approval_status = "NOT_SUBMITTED"
            profile.access_status = "ACTIVE"
            profile.verified_at = None
            profile.save(update_fields=["email_verified", "approval_status", "access_status", "verified_at"])

            return user


class VerifyEmailOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(
        required=True,
        min_length=6,
        max_length=6,
        trim_whitespace=True,
    )

    def validate_email(self, value):
        return value.strip().lower()

    def validate_otp(self, value):
        value = value.strip()
        if not value.isdigit() or len(value) != 6:
            raise serializers.ValidationError("OTP must be a 6-digit numeric code.")
        return value


class ResendEmailOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        return value.strip().lower()


class UnverifiedUserLoginError(serializers.ValidationError):
    def __init__(self, detail, email):
        super().__init__({"detail": detail, "code": "EMAIL_NOT_VERIFIED", "email": email})


class OwnerLoginSerializer(serializers.Serializer):
    identifier = serializers.CharField(trim_whitespace=True)
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )

    default_error = "Invalid username/email or password."

    def validate(self, attrs):
        identifier = attrs["identifier"].strip()
        password = attrs["password"]
        request = self.context.get("request")

        # Allow login by username (case-insensitive) OR email (case-insensitive)
        user = User.objects.filter(username__iexact=identifier).first()
        if not user:
            user = User.objects.filter(email__iexact=identifier).first()

        if user is not None:
            # Check password directly
            if user.check_password(password):
                # Ensure active status is aligned
                if not user.is_active:
                    user.is_active = True
                    user.save(update_fields=["is_active"])

                authenticated_user = authenticate(
                    request=request,
                    username=user.username,
                    password=password,
                )

                if authenticated_user is None:
                    authenticated_user = user

                attrs["user"] = authenticated_user
                return attrs

        raise serializers.ValidationError(
            {"detail": self.default_error}
        )


ALLOWED_DOCUMENT_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
MAX_DOCUMENT_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


def validate_verification_document(file_obj, field_name: str):
    """
    Validates file extension and maximum allowable size.
    Prevents executable uploads and oversized payloads.
    """
    if not file_obj:
        return
    import os
    ext = os.path.splitext(file_obj.name)[1].lower()
    if ext not in ALLOWED_DOCUMENT_EXTENSIONS:
        raise serializers.ValidationError(
            f"{field_name}: Unsupported file format '{ext}'. Allowed formats are PDF, PNG, and JPEG."
        )
    if file_obj.size > MAX_DOCUMENT_SIZE_BYTES:
        raise serializers.ValidationError(
            f"{field_name}: File size ({file_obj.size / (1024 * 1024):.1f} MB) exceeds maximum limit of 10 MB."
        )


class OwnerVerificationRequestSerializer(serializers.ModelSerializer):
    ownership_proof = serializers.FileField(required=True)
    utility_bill = serializers.FileField(required=False, allow_null=True)
    authorization_letter = serializers.FileField(required=False, allow_null=True)

    owner_username = serializers.CharField(source="owner.username", read_only=True)
    owner_email = serializers.CharField(source="owner.email", read_only=True)
    reviewed_by_username = serializers.CharField(
        source="reviewed_by.username", read_only=True, default=""
    )

    class Meta:
        from .models import OwnerVerificationRequest
        model = OwnerVerificationRequest
        fields = [
            "id",
            "owner",
            "owner_username",
            "owner_email",
            "property_name",
            "address",
            "city",
            "state",
            "postal_code",
            "property_type",
            "relationship",
            "ownership_proof",
            "utility_bill",
            "authorization_letter",
            "notes",
            "status",
            "submitted_at",
            "reviewed_at",
            "reviewed_by_username",
            "owner_facing_message",
            "rejection_reason",
        ]
        read_only_fields = [
            "id",
            "owner",
            "owner_username",
            "owner_email",
            "status",
            "submitted_at",
            "reviewed_at",
            "reviewed_by_username",
            "owner_facing_message",
            "rejection_reason",
        ]

    def validate_ownership_proof(self, value):
        validate_verification_document(value, "ownership_proof")
        return value

    def validate_utility_bill(self, value):
        validate_verification_document(value, "utility_bill")
        return value

    def validate_authorization_letter(self, value):
        validate_verification_document(value, "authorization_letter")
        return value

    def validate(self, attrs):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Authentication required.")

        user = request.user
        profile = getattr(user, "profile", None)

        # 1. Require verified email before submitting property verification
        if not profile or not profile.email_verified:
            raise serializers.ValidationError(
                "You must verify your email address via OTP before submitting property ownership verification."
            )

        return attrs

    def create(self, validated_data):
        from .models import OwnerVerificationRequest, OwnerAuditLog, OwnerProfile
        request = self.context.get("request")
        user = request.user
        validated_data["owner"] = user
        validated_data["status"] = "PENDING"

        with transaction.atomic():
            # Update existing pending request if present, or create new
            existing_req = OwnerVerificationRequest.objects.filter(owner=user, status="PENDING").order_by("-submitted_at").first()
            if existing_req:
                for attr, val in validated_data.items():
                    setattr(existing_req, attr, val)
                existing_req.submitted_at = timezone.now()
                existing_req.save()
                instance = existing_req
            else:
                instance = OwnerVerificationRequest.objects.create(**validated_data)

            # Update owner profile status to PENDING
            profile, _ = OwnerProfile.objects.get_or_create(user=user)
            profile.approval_status = "PENDING"
            profile.owner_facing_message = "Your property verification request is under review."
            profile.save(update_fields=["approval_status", "owner_facing_message", "updated_at"])

            # Log audit record
            ip_address = request.META.get("REMOTE_ADDR")
            OwnerAuditLog.objects.create(
                owner=user,
                performed_by=user,
                action="REQUEST_SUBMITTED",
                notes=f"Submitted/Updated verification request #{instance.id} for property '{instance.property_name}'.",
                ip_address=ip_address,
            )

            return instance


class AdminVerificationReviewSerializer(serializers.Serializer):
    action = serializers.ChoiceField(
        choices=["APPROVE", "REJECT", "REQUEST_MORE_INFO"],
        required=True,
    )
    owner_facing_message = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )
    internal_notes = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )
    rejection_reason = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )

    def validate(self, attrs):
        action = attrs.get("action")
        if action == "REJECT" and not attrs.get("rejection_reason") and not attrs.get("owner_facing_message"):
            raise serializers.ValidationError(
                {"rejection_reason": "An explanation is required when rejecting a verification request."}
            )
        if action == "REQUEST_MORE_INFO" and not attrs.get("owner_facing_message"):
            raise serializers.ValidationError(
                {"owner_facing_message": "Please specify the additional documents or details required from the owner."}
            )
        return attrs


class AdminOwnerAccessSerializer(serializers.Serializer):
    action = serializers.ChoiceField(
        choices=["grant", "approve", "suspend", "hold", "restore", "revoke", "reject"],
        required=True,
    )
    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )
    internal_notes = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )

    def validate(self, attrs):
        action = attrs.get("action")
        if action in ("suspend", "hold", "revoke", "reject") and not attrs.get("reason"):
            raise serializers.ValidationError(
                {"reason": f"An administrator explanation note is required to {action} owner access."}
            )
        return attrs


class OwnerAuditLogSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source="owner.username", read_only=True)
    performed_by_username = serializers.CharField(
        source="performed_by.username", read_only=True, default="System"
    )

    class Meta:
        from .models import OwnerAuditLog
        model = OwnerAuditLog
        fields = [
            "id",
            "owner",
            "owner_username",
            "performed_by_username",
            "action",
            "notes",
            "ip_address",
            "created_at",
        ]
        read_only_fields = fields

