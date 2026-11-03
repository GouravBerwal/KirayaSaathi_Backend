import logging
from django.conf import settings
from django.contrib.auth import get_user_model, login, logout

logger = logging.getLogger(__name__)
from django.db import transaction
from django.middleware.csrf import get_token
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect

from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import EmailOTPChallenge, OwnerProfile, OwnerVerificationRequest, OwnerAuditLog
from .serializers import (
    OwnerRegistrationSerializer,
    OwnerLoginSerializer,
    VerifyEmailOTPSerializer,
    ResendEmailOTPSerializer,
    UnverifiedEmailError,
)
from .services import (
    OTP_EXPIRY_MINUTES,
    OTP_RESEND_COOLDOWN_SECONDS,
    check_rate_limits,
    get_remaining_cooldown,
    issue_otp_challenge,
    mask_email,
    verify_otp_hash,
)

User = get_user_model()


def get_client_ip(request) -> str:
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


@method_decorator(csrf_protect, name="dispatch")
class OwnerRegistrationView(APIView):
    """
    Register a new owner and initiate email OTP verification.
    POST /api/auth/register/ (alias /api/auth/signup/)
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = OwnerRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ip_address = get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")

        try:
            with transaction.atomic():
                user = serializer.save()
                challenge, otp = issue_otp_challenge(
                    user=user,
                    email=user.email,
                    ip_address=ip_address,
                    user_agent=user_agent,
                )
        except Exception as e:
            logger.exception("Owner registration failed: %s", e)
            return Response(
                {
                    "detail": "Failed to send verification email. Please check your email and try again.",
                    "code": "EMAIL_DELIVERY_FAILED",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        email_sent = getattr(challenge, "email_sent", False)
        if not email_sent:
            return Response(
                {
                    "detail": f"Failed to deliver verification email to {user.email}. Please verify your email address and try again.",
                    "code": "EMAIL_DELIVERY_FAILED",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        response_data = {
            "detail": "Registration initiated. Verification code sent to your email.",
            "email": user.email,
            "masked_email": mask_email(user.email),
            "cooldown_seconds": OTP_RESEND_COOLDOWN_SECONDS,
            "expires_in_minutes": OTP_EXPIRY_MINUTES,
        }

        return Response(response_data, status=status.HTTP_201_CREATED)


@method_decorator(csrf_protect, name="dispatch")
class VerifyEmailOTPView(APIView):
    """
    Verify the 6-digit OTP code sent to owner's email address.
    POST /api/auth/verify-email-otp/
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = VerifyEmailOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]

        with transaction.atomic():
            challenge = (
                EmailOTPChallenge.objects.select_for_update()
                .filter(email__iexact=email, is_consumed=False)
                .order_by("-created_at")
                .first()
            )

            if not challenge:
                return Response(
                    {
                        "detail": "Verification code has expired or is invalid. Please request a new code.",
                        "code": "OTP_NOT_FOUND",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if challenge.is_expired():
                challenge.is_consumed = True
                challenge.save(update_fields=["is_consumed"])
                return Response(
                    {
                        "detail": "Verification code has expired. Please request a new code.",
                        "code": "OTP_EXPIRED",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if challenge.has_exceeded_attempts():
                challenge.is_consumed = True
                challenge.save(update_fields=["is_consumed"])
                return Response(
                    {
                        "detail": "Maximum verification attempts exceeded. Please request a new code.",
                        "code": "MAX_ATTEMPTS_EXCEEDED",
                        "attempts_remaining": 0,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            is_valid = verify_otp_hash(email, otp, challenge.otp_hash)

            if not is_valid:
                challenge.attempts += 1
                if challenge.attempts >= challenge.max_attempts:
                    challenge.is_consumed = True
                challenge.save(update_fields=["attempts", "is_consumed"])

                remaining = max(0, challenge.max_attempts - challenge.attempts)
                if remaining == 0:
                    return Response(
                        {
                            "detail": "Maximum verification attempts exceeded. Please request a new code.",
                            "code": "MAX_ATTEMPTS_EXCEEDED",
                            "attempts_remaining": 0,
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                return Response(
                    {
                        "detail": f"Invalid verification code. {remaining} attempt(s) remaining.",
                        "code": "INVALID_OTP",
                        "attempts_remaining": remaining,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # OTP is valid!
            challenge.is_consumed = True
            challenge.consumed_at = timezone.now()
            challenge.save(update_fields=["is_consumed", "consumed_at"])

            # Invalidate all prior challenges for this email
            EmailOTPChallenge.objects.filter(
                email__iexact=email,
                is_consumed=False,
            ).update(is_consumed=True)

            user = challenge.user or User.objects.filter(email__iexact=email).first()
            if not user:
                return Response(
                    {"detail": "User account not found.", "code": "USER_NOT_FOUND"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            user.is_active = True
            user.save(update_fields=["is_active"])

            profile, _ = OwnerProfile.objects.get_or_create(user=user)
            profile.email_verified = True
            profile.verified_at = timezone.now()
            if profile.approval_status not in ("APPROVED", "REJECTED", "NEEDS_MORE_INFORMATION"):
                profile.approval_status = "PENDING"
                profile.owner_facing_message = "Your verification request is under review."
            profile.save(update_fields=["email_verified", "verified_at", "approval_status", "owner_facing_message"])

            # Auto-create or ensure OwnerVerificationRequest exists so it IMMEDIATELY appears on the Admin Panel!
            ver_req, created = OwnerVerificationRequest.objects.get_or_create(
                owner=user,
                defaults={
                    "property_name": f"{user.username}'s Property",
                    "address": "Submitted via Owner Registration",
                    "city": "Indore",
                    "state": "Madhya Pradesh",
                    "postal_code": "452001",
                    "property_type": "BUILDING",
                    "relationship": "OWNER",
                    "status": "PENDING",
                    "notes": "Automatically created upon email OTP verification.",
                },
            )
            if not created and ver_req.status not in ("APPROVED", "REJECTED"):
                ver_req.status = "PENDING"
                ver_req.save(update_fields=["status"])

            # Log the owner in to establish session
            login(request._request, user)

            return Response(
                {
                    "detail": "Email verified successfully.",
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "email_verified": True,
                    },
                },
                status=status.HTTP_200_OK,
            )


@method_decorator(csrf_protect, name="dispatch")
class ResendEmailOTPView(APIView):
    """
    Resend a new OTP verification code to the owner's email address.
    POST /api/auth/resend-email-otp/
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = ResendEmailOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        user = User.objects.filter(email__iexact=email).first()
        if user and getattr(getattr(user, "profile", None), "email_verified", False):
            return Response(
                {
                    "detail": "This email address is already verified. Please sign in.",
                    "code": "ALREADY_VERIFIED",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Enforce hourly rate limits first
        ip_address = get_client_ip(request)
        is_allowed, error_msg = check_rate_limits(email, ip_address)
        if not is_allowed:
            return Response(
                {
                    "detail": error_msg,
                    "code": "RATE_LIMITED",
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        # Enforce 60-second resend cooldown
        remaining_cooldown = get_remaining_cooldown(email)
        if remaining_cooldown > 0:
            return Response(
                {
                    "detail": f"Please wait {remaining_cooldown} seconds before requesting a new code.",
                    "code": "COOLDOWN_ACTIVE",
                    "cooldown_seconds": remaining_cooldown,
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        # Issue new challenge if user exists
        challenge = None
        otp = ""
        email_sent = True
        if user:
            user_agent = request.META.get("HTTP_USER_AGENT", "")
            try:
                challenge, otp = issue_otp_challenge(
                    user=user,
                    email=email,
                    ip_address=ip_address,
                    user_agent=user_agent,
                )
                email_sent = getattr(challenge, "email_sent", True)
            except Exception as e:
                logger.exception("Resend OTP failed: %s", e)
                return Response(
                    {
                        "detail": "Failed to send verification email. Please try again.",
                        "code": "EMAIL_DELIVERY_FAILED",
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        if not email_sent:
            return Response(
                {
                    "detail": f"Failed to send verification email to {email}. Please try again later.",
                    "code": "EMAIL_DELIVERY_FAILED",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        response_data = {
            "detail": "A new 6-digit verification code has been sent to your email.",
            "email": email,
            "masked_email": mask_email(email),
            "cooldown_seconds": OTP_RESEND_COOLDOWN_SECONDS,
            "expires_in_minutes": OTP_EXPIRY_MINUTES,
        }

        return Response(
            response_data,
            status=status.HTTP_200_OK,
        )


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CSRFTokenView(APIView):
    """
    Set a CSRF cookie before React submits login or signup.
    GET /api/auth/csrf/
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        token = get_token(request)
        return Response(
            {
                "detail": "CSRF cookie set.",
                "csrfToken": token,
            },
            status=status.HTTP_200_OK,
        )


@method_decorator(csrf_protect, name="dispatch")
class OwnerLoginView(APIView):
    """
    Login using username or email and password.
    POST /api/auth/login/
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = OwnerLoginSerializer(
            data=request.data,
            context={"request": request},
        )
        try:
            serializer.is_valid(raise_exception=True)
        except UnverifiedEmailError as e:
            return Response(e.detail, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as e:
            raise e

        user = serializer.validated_data["user"]
        login(request._request, user)

        return Response(
            {
                "detail": "Login successful.",
                "csrfToken": get_token(request._request),
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "email_verified": getattr(getattr(user, "profile", None), "email_verified", True),
                },
            },
            status=status.HTTP_200_OK,
        )


@method_decorator(csrf_protect, name="dispatch")
class OwnerLogoutView(APIView):
    """
    Logout the currently logged-in owner.
    POST /api/auth/logout/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request._request)

        return Response(
            {"detail": "Logout successful."},
            status=status.HTTP_200_OK,
        )


class OwnerMeView(APIView):
    """
    Return the currently logged-in user's details, approval status, and access status.
    GET /api/auth/me/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        first_name = (user.first_name or "").strip()
        last_name = (user.last_name or "").strip()
        full_name = f"{first_name} {last_name}".strip()
        
        profile = getattr(user, "profile", None)
        email_verified = getattr(profile, "email_verified", False)
        approval_status = getattr(profile, "approval_status", "NOT_SUBMITTED")
        access_status = getattr(profile, "access_status", "ACTIVE")
        is_authorized = bool(profile and profile.is_owner_authorized()) or bool(user.is_staff or user.is_superuser)
        owner_facing_message = getattr(profile, "owner_facing_message", "")
        suspension_reason = getattr(profile, "suspension_reason", "")
        revocation_reason = getattr(profile, "revocation_reason", "")

        latest_req = None
        if hasattr(user, "verification_requests"):
            latest_req = user.verification_requests.order_by("-submitted_at").first()

        rejection_reason = revocation_reason or (latest_req.rejection_reason if latest_req else "")

        latest_req_data = None
        if latest_req:
            latest_req_data = {
                "id": latest_req.id,
                "property_name": latest_req.property_name,
                "city": latest_req.city,
                "status": latest_req.status,
                "submitted_at": latest_req.submitted_at,
                "owner_facing_message": latest_req.owner_facing_message,
                "rejection_reason": latest_req.rejection_reason,
            }

        return Response(
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": first_name,
                "last_name": last_name,
                "full_name": full_name,
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser,
                "email_verified": email_verified,
                "approval_status": approval_status,
                "access_status": access_status,
                "is_authorized": is_authorized,
                "owner_facing_message": owner_facing_message,
                "suspension_reason": suspension_reason,
                "revocation_reason": revocation_reason,
                "rejection_reason": rejection_reason,
                "latest_request": latest_req_data,
            },
            status=status.HTTP_200_OK,
        )


import mimetypes
from django.http import FileResponse, Http404
from django.db.models import Q
from .permissions import IsAdminOrStaffUser
from .models import OwnerVerificationRequest, OwnerAuditLog
from .serializers import (
    OwnerVerificationRequestSerializer,
    AdminVerificationReviewSerializer,
    AdminOwnerAccessSerializer,
    OwnerAuditLogSerializer,
)
from .services import (
    send_owner_approval_email,
    send_owner_rejection_email,
    send_owner_more_info_email,
    send_owner_suspension_email,
    send_owner_restoration_email,
    send_owner_revocation_email,
    send_verification_request_received_email,
)


class OwnerVerificationRequestListCreateView(APIView):
    """
    Owner submits or lists their property ownership verification requests.
    GET, POST /api/auth/verification-requests/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        requests_qs = OwnerVerificationRequest.objects.filter(
            owner=request.user
        ).order_by("-submitted_at")
        serializer = OwnerVerificationRequestSerializer(
            requests_qs,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        profile = getattr(request.user, "profile", None)
        if not profile or not profile.email_verified:
            return Response(
                {
                    "detail": "Email verification is required before you can submit a property verification request.",
                    "code": "EMAIL_VERIFICATION_REQUIRED",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = OwnerVerificationRequestSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        # Send confirmation email
        send_verification_request_received_email(
            email=request.user.email,
            username=request.user.username,
            property_name=instance.property_name,
        )

        return Response(
            {
                "detail": "Property verification request submitted successfully. Our administrative team will review your documents.",
                "request": serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )


class OwnerVerificationRequestDetailView(APIView):
    """
    Retrieve single verification request by owner or administrator.
    GET /api/auth/verification-requests/<int:pk>/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            req_obj = OwnerVerificationRequest.objects.get(pk=pk)
        except OwnerVerificationRequest.DoesNotExist:
            return Response({"detail": "Verification request not found."}, status=status.HTTP_404_NOT_FOUND)

        if not (request.user.is_staff or request.user.is_superuser or req_obj.owner == request.user):
            return Response({"detail": "You do not have permission to view this request."}, status=status.HTTP_403_FORBIDDEN)

        serializer = OwnerVerificationRequestSerializer(req_obj, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class SecureDocumentDownloadView(APIView):
    """
    Secure file streaming for property verification evidence.
    Access is restricted exclusively to administrators or the owning applicant.
    GET /api/auth/verification-requests/<int:pk>/document/<str:doc_type>/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, doc_type):
        try:
            req_obj = OwnerVerificationRequest.objects.get(pk=pk)
        except OwnerVerificationRequest.DoesNotExist:
            raise Http404("Verification request not found.")

        # Strict authorization check
        if not (request.user.is_staff or request.user.is_superuser or req_obj.owner == request.user):
            return Response(
                {"detail": "You do not have authorization to access this verification document."},
                status=status.HTTP_403_FORBIDDEN,
            )

        allowed_fields = ["ownership_proof", "utility_bill", "authorization_letter"]
        if doc_type not in allowed_fields:
            raise Http404("Invalid document type requested.")

        file_field = getattr(req_obj, doc_type, None)
        if not file_field or not file_field.name:
            raise Http404("Document was not provided or has been removed.")

        try:
            file_handle = file_field.open("rb")
        except Exception:
            raise Http404("Document file could not be read from storage.")

        content_type, _ = mimetypes.guess_type(file_field.name)
        if not content_type:
            content_type = "application/octet-stream"

        response = FileResponse(file_handle, content_type=content_type)
        response["Content-Disposition"] = f'inline; filename="{file_field.name.split("/")[-1]}"'
        return response


# ==============================================================================
# DEDICATED ADMINISTRATOR ENDPOINTS
# ==============================================================================

class AdminVerificationRequestListView(APIView):
    """
    Admin endpoint to view, search, and filter all owner verification requests.
    GET /api/admin/verification-requests/
    """
    permission_classes = [IsAdminOrStaffUser]

    def get(self, request):
        # Auto-create verification request for any verified owner who doesn't have one yet
        owners_without_req = User.objects.filter(
            profile__email_verified=True,
            is_staff=False,
            is_superuser=False,
            verification_requests__isnull=True,
        )
        for u in owners_without_req:
            p = getattr(u, "profile", None)
            cur_status = getattr(p, "approval_status", "PENDING")
            if cur_status not in ("APPROVED", "REJECTED", "NEEDS_MORE_INFORMATION"):
                cur_status = "PENDING"
            owned = getattr(u, "owned_properties", None)
            first_property = owned.first() if owned is not None else None
            prop_name = (
                first_property.name
                if first_property is not None
                else f"{u.username}'s Property"
            )
            OwnerVerificationRequest.objects.create(
                owner=u,
                property_name=prop_name,
                address="Owner Account Verification",
                city="Indore",
                state="Madhya Pradesh",
                postal_code="452001",
                property_type="BUILDING",
                relationship="OWNER",
                status=cur_status,
                notes="Auto-populated for administrative review.",
            )

        qs = OwnerVerificationRequest.objects.select_related("owner", "reviewed_by").all().order_by("-submitted_at")

        status_param = request.query_params.get("status")
        if status_param:
            qs = qs.filter(status__iexact=status_param.strip())

        search_param = request.query_params.get("q")
        if search_param:
            term = search_param.strip()
            qs = qs.filter(
                Q(owner__username__icontains=term)
                | Q(owner__email__icontains=term)
                | Q(property_name__icontains=term)
                | Q(city__icontains=term)
            )

        serializer = OwnerVerificationRequestSerializer(qs, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminVerificationReviewActionView(APIView):
    """
    Admin endpoint to approve, reject, or request more information on a request.
    POST /api/admin/verification-requests/<int:pk>/review/
    """
    permission_classes = [IsAdminOrStaffUser]

    def post(self, request, pk):
        serializer = AdminVerificationReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action = serializer.validated_data["action"]
        owner_msg = serializer.validated_data.get("owner_facing_message", "")
        internal_notes = serializer.validated_data.get("internal_notes", "")
        rejection_reason = serializer.validated_data.get("rejection_reason", "")
        admin_user = request.user
        ip_addr = get_client_ip(request)

        with transaction.atomic():
            try:
                req_obj = OwnerVerificationRequest.objects.select_for_update().get(pk=pk)
            except OwnerVerificationRequest.DoesNotExist:
                return Response({"detail": "Verification request not found."}, status=status.HTTP_404_NOT_FOUND)

            owner = req_obj.owner
            profile, _ = OwnerProfile.objects.get_or_create(user=owner)
            if action == "APPROVE":
                # Confirm owner has verified email
                if not profile.email_verified:
                    return Response(
                        {"detail": "Cannot approve an owner whose email address has not been verified."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                is_first_approval = profile.approval_status != "APPROVED"

                req_obj.status = "APPROVED"
                req_obj.reviewed_at = timezone.now()
                req_obj.reviewed_by = admin_user
                req_obj.internal_notes = internal_notes
                req_obj.owner_facing_message = owner_msg or "Your property verification has been approved."
                req_obj.save()

                profile.approval_status = "APPROVED"
                profile.approved_at = timezone.now()
                profile.approved_by = admin_user
                profile.access_status = "ACTIVE"
                profile.owner_facing_message = req_obj.owner_facing_message
                profile.internal_notes = internal_notes
                profile.save()

                # Audit log
                OwnerAuditLog.objects.create(
                    owner=owner,
                    performed_by=admin_user,
                    action="APPROVED",
                    notes=f"Approved verification request #{req_obj.id} for property '{req_obj.property_name}'.",
                    ip_address=ip_addr,
                )

                # Send approval email once (idempotent)
                if is_first_approval:
                    send_owner_approval_email(owner.email, owner.username, req_obj.property_name)

                return Response(
                    {"detail": "Verification request approved successfully. Owner workspace is active.", "status": "APPROVED"},
                    status=status.HTTP_200_OK,
                )

            elif action == "REJECT":
                reason = rejection_reason or owner_msg or "Verification documentation did not meet platform criteria."
                req_obj.status = "REJECTED"
                req_obj.reviewed_at = timezone.now()
                req_obj.reviewed_by = admin_user
                req_obj.internal_notes = internal_notes
                req_obj.owner_facing_message = reason
                req_obj.rejection_reason = reason
                req_obj.save()

                profile.approval_status = "REJECTED"
                profile.access_status = "REVOKED"
                profile.revocation_reason = reason
                profile.owner_facing_message = reason
                profile.save()

                OwnerAuditLog.objects.create(
                    owner=owner,
                    performed_by=admin_user,
                    action="REJECTED",
                    notes=f"Rejected request #{req_obj.id}. Reason: {reason}",
                    ip_address=ip_addr,
                )

                send_owner_rejection_email(owner.email, owner.username, req_obj.property_name, reason)

                return Response(
                    {"detail": "Verification request rejected.", "status": "REJECTED"},
                    status=status.HTTP_200_OK,
                )

            elif action == "REQUEST_MORE_INFO":
                req_obj.status = "NEEDS_MORE_INFORMATION"
                req_obj.reviewed_at = timezone.now()
                req_obj.reviewed_by = admin_user
                req_obj.internal_notes = internal_notes
                req_obj.owner_facing_message = owner_msg
                req_obj.save()

                profile.approval_status = "NEEDS_MORE_INFORMATION"
                profile.access_status = "SUSPENDED"
                profile.suspension_reason = owner_msg
                profile.owner_facing_message = owner_msg
                profile.save()

                OwnerAuditLog.objects.create(
                    owner=owner,
                    performed_by=admin_user,
                    action="MORE_INFO_REQUESTED",
                    notes=f"Requested more information for request #{req_obj.id}: {owner_msg}",
                    ip_address=ip_addr,
                )

                send_owner_more_info_email(owner.email, owner.username, req_obj.property_name, owner_msg)

                return Response(
                    {"detail": "Additional information requested from owner.", "status": "NEEDS_MORE_INFORMATION"},
                    status=status.HTTP_200_OK,
                )


class AdminOwnerListView(APIView):
    """
    Admin endpoint to view all owners, their verification status, approval status, and access status.
    GET /api/admin/owners/
    """
    permission_classes = [IsAdminOrStaffUser]

    def get(self, request):
        owners = User.objects.select_related("profile").prefetch_related("owned_properties").all().order_by("-id")

        search = request.query_params.get("q")
        if search:
            s = search.strip()
            owners = owners.filter(
                Q(username__icontains=s) | Q(email__icontains=s) | Q(first_name__icontains=s) | Q(last_name__icontains=s)
            )

        data = []
        for u in owners:
            p = getattr(u, "profile", None)
            data.append(
                {
                    "id": u.id,
                    "username": u.username,
                    "email": u.email,
                    "full_name": f"{u.first_name} {u.last_name}".strip() or u.username,
                    "is_staff": u.is_staff,
                    "is_superuser": u.is_superuser,
                    "is_active": u.is_active,
                    "email_verified": getattr(p, "email_verified", False),
                    "approval_status": getattr(p, "approval_status", "NOT_SUBMITTED"),
                    "access_status": getattr(p, "access_status", "ACTIVE"),
                    "approved_at": getattr(p, "approved_at", None),
                    "approved_by": p.approved_by.username if p and p.approved_by else None,
                    "suspension_reason": getattr(p, "suspension_reason", ""),
                    "revocation_reason": getattr(p, "revocation_reason", ""),
                    "properties_count": u.owned_properties.count() if hasattr(u, "owned_properties") else 0,
                    "date_joined": u.date_joined,
                }
            )

        return Response(data, status=status.HTTP_200_OK)


class AdminOwnerAccessActionView(APIView):
    """
    Admin endpoint to grant, suspend, restore, or revoke owner access.
    POST /api/admin/owners/<int:user_id>/manage-access/
    """
    permission_classes = [IsAdminOrStaffUser]

    def post(self, request, user_id):
        try:
            target_user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"detail": "Owner user not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = AdminOwnerAccessSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action = serializer.validated_data["action"]
        reason = serializer.validated_data.get("reason", "")
        internal_notes = serializer.validated_data.get("internal_notes", "")

        admin_user = request.user
        ip_addr = get_client_ip(request)

        # Safety Guard 1: Administrator cannot suspend or revoke themselves
        if target_user.id == admin_user.id and action in ("suspend", "revoke"):
            return Response(
                {"detail": "Safety Violation: You cannot suspend or revoke your own administrative account."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Safety Guard 2: Cannot suspend or revoke the last superuser
        if target_user.is_superuser and action in ("suspend", "revoke"):
            superuser_count = User.objects.filter(is_superuser=True, is_active=True).count()
            if superuser_count <= 1:
                return Response(
                    {"detail": "Safety Violation: Cannot suspend or revoke the last active superuser."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        profile, _ = OwnerProfile.objects.get_or_create(user=target_user)

        with transaction.atomic():
            if action in ("suspend", "hold"):
                profile.access_status = "SUSPENDED"
                profile.approval_status = "NEEDS_MORE_INFORMATION"
                profile.suspended_at = timezone.now()
                profile.suspension_reason = reason
                profile.owner_facing_message = reason
                profile.internal_notes = internal_notes
                profile.save()

                target_user.verification_requests.all().update(
                    status="NEEDS_MORE_INFORMATION",
                    reviewed_at=timezone.now(),
                    reviewed_by=admin_user,
                    owner_facing_message=reason,
                )

                OwnerAuditLog.objects.create(
                    owner=target_user,
                    performed_by=admin_user,
                    action="SUSPENDED",
                    notes=f"Put owner access on hold/suspended. Reason: {reason}",
                    ip_address=ip_addr,
                )

                send_owner_suspension_email(target_user.email, target_user.username, reason)

                return Response(
                    {"detail": f"Owner '{target_user.username}' account put on hold / suspended.", "access_status": "SUSPENDED"},
                    status=status.HTTP_200_OK,
                )

            elif action in ("reject", "revoke"):
                profile.approval_status = "REJECTED"
                profile.access_status = "REVOKED"
                profile.revoked_at = timezone.now()
                profile.revocation_reason = reason
                profile.owner_facing_message = reason
                profile.internal_notes = internal_notes
                profile.save()

                target_user.verification_requests.all().update(
                    status="REJECTED",
                    reviewed_at=timezone.now(),
                    reviewed_by=admin_user,
                    rejection_reason=reason,
                    owner_facing_message=reason,
                )

                OwnerAuditLog.objects.create(
                    owner=target_user,
                    performed_by=admin_user,
                    action="REVOKED",
                    notes=f"Rejected owner account / Revoked access. Reason: {reason}",
                    ip_address=ip_addr,
                )

                send_owner_rejection_email(target_user.email, target_user.username, "", reason)

                return Response(
                    {"detail": f"Owner '{target_user.username}' account rejected and access revoked.", "access_status": "REVOKED", "approval_status": "REJECTED"},
                    status=status.HTTP_200_OK,
                )

            elif action in ("grant", "approve"):
                if not profile.email_verified:
                    return Response(
                        {"detail": "Owner email address must be verified before granting approval."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                profile.approval_status = "APPROVED"
                profile.access_status = "ACTIVE"
                profile.approved_at = timezone.now()
                profile.approved_by = admin_user
                profile.owner_facing_message = reason or "Your workspace has been approved."
                profile.internal_notes = internal_notes
                profile.save()

                target_user.verification_requests.filter(status__in=["PENDING", "NEEDS_MORE_INFORMATION", "REJECTED"]).update(
                    status="APPROVED",
                    reviewed_at=timezone.now(),
                    reviewed_by=admin_user,
                    owner_facing_message="Your property verification request has been approved.",
                )

                OwnerAuditLog.objects.create(
                    owner=target_user,
                    performed_by=admin_user,
                    action="APPROVED",
                    notes="Directly granted owner access by administrator.",
                    ip_address=ip_addr,
                )

                send_owner_approval_email(target_user.email, target_user.username)

                return Response(
                    {"detail": f"Access granted to owner '{target_user.username}'.", "approval_status": "APPROVED", "access_status": "ACTIVE"},
                    status=status.HTTP_200_OK,
                )

            elif action == "restore":
                profile.approval_status = "APPROVED"
                profile.access_status = "ACTIVE"
                profile.suspended_at = None
                profile.suspension_reason = ""
                profile.owner_facing_message = "Your workspace access has been restored."
                profile.save()

                target_user.verification_requests.filter(status__in=["NEEDS_MORE_INFORMATION"]).update(
                    status="APPROVED",
                    reviewed_at=timezone.now(),
                    reviewed_by=admin_user,
                )

                OwnerAuditLog.objects.create(
                    owner=target_user,
                    performed_by=admin_user,
                    action="RESTORED",
                    notes="Restored owner access.",
                    ip_address=ip_addr,
                )

                send_owner_restoration_email(target_user.email, target_user.username)

                return Response(
                    {"detail": f"Owner '{target_user.username}' access has been restored.", "access_status": "ACTIVE"},
                    status=status.HTTP_200_OK,
                )


class AdminAuditLogListView(APIView):
    """
    Admin endpoint to view chronological audit trail of all sensitive events.
    GET /api/admin/audit-logs/
    """
    permission_classes = [IsAdminOrStaffUser]

    def get(self, request):
        logs = OwnerAuditLog.objects.select_related("owner", "performed_by").all().order_by("-created_at")[:200]
        serializer = OwnerAuditLogSerializer(logs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ContactInquiryView(APIView):
    """
    Public endpoint to submit customer inquiries from the landing page.
    POST /api/auth/contact/
    """
    permission_classes = [AllowAny]

    def post(self, request):
        name = request.data.get("name", "").strip()
        email = request.data.get("email", "").strip()
        phone = request.data.get("phone", "").strip()
        property_type = request.data.get("property_type", "").strip()
        message = request.data.get("message", "").strip()

        if not name or (not email and not phone):
            return Response(
                {"detail": "Please provide your name and at least an email address or phone number."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "detail": "Thank you! Your inquiry has been received. Our KirayaSetu support team will contact you shortly.",
                "status": "SUCCESS",
            },
            status=status.HTTP_200_OK,
        )


from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.contrib.auth import authenticate
from .authentication import ADMIN_SIGNER_SALT


class AdminTokenLoginView(APIView):
    """
    Dedicated Admin Login endpoint.
    Returns a signed admin token header for the Admin Console.
    CRITICAL: Does NOT call login(request, user), so it does NOT send a sessionid cookie.
    This guarantees that the active browser session of any currently registered/logged-in
    property owner remains 100% UNTOUCHED!
    POST /api/admin/auth/login/
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        identifier = str(request.data.get("identifier", "")).strip()
        password = str(request.data.get("password", ""))

        if not identifier or not password:
            return Response(
                {"detail": "Administrator username/email and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = None
        if "@" in identifier:
            user_obj = User.objects.filter(email__iexact=identifier).first()
            if user_obj:
                user = authenticate(request=request._request, username=user_obj.username, password=password)
        else:
            user = authenticate(request=request._request, username=identifier, password=password)

        if not user:
            return Response(
                {"detail": "Invalid administrator credentials. Please check your username and password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not (user.is_staff or user.is_superuser):
            return Response(
                {"detail": "Access Denied: This portal requires administrator or staff privileges."},
                status=status.HTTP_403_FORBIDDEN,
            )

        signer = TimestampSigner(salt=ADMIN_SIGNER_SALT)
        admin_token = signer.sign_object({"user_id": user.id, "username": user.username})

        return Response(
            {
                "detail": "Admin authorized successfully.",
                "admin_token": admin_token,
                "admin_user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "is_staff": user.is_staff,
                    "is_superuser": user.is_superuser,
                },
            },
            status=status.HTTP_200_OK,
        )


class AdminTokenMeView(APIView):
    """
    Check administrator token authorization status.
    GET /api/admin/auth/me/
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        token = request.headers.get("X-Admin-Token") or request.META.get("HTTP_X_ADMIN_TOKEN")
        if not token:
            return Response({"authenticated": False}, status=status.HTTP_401_UNAUTHORIZED)

        signer = TimestampSigner(salt=ADMIN_SIGNER_SALT)
        try:
            data = signer.unsign_object(token, max_age=86400)
            user_id = data.get("user_id")
            user = User.objects.filter(id=user_id, is_active=True).first()
            if user and (user.is_staff or user.is_superuser):
                return Response({
                    "authenticated": True,
                    "admin_user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "is_staff": user.is_staff,
                        "is_superuser": user.is_superuser,
                    }
                })
        except (BadSignature, SignatureExpired):
            pass

        return Response({"authenticated": False}, status=status.HTTP_401_UNAUTHORIZED)


