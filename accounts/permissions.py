from rest_framework.permissions import BasePermission


class IsVerifiedOwner(BasePermission):
    """
    Strict central authorization policy:
    An owner may access protected owner functionality only when all conditions are true:
    1. Authenticated
    2. Email verified via OTP
    3. Property ownership request approved by Administrator (approval_status == 'APPROVED')
    4. Account operational status is active (access_status == 'ACTIVE')
    
    Superusers and staff members bypass owner verification checks for admin work.
    """
    message = "Access restricted. You must be an email-verified, admin-approved active owner."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if user.is_staff or user.is_superuser:
            return True

        profile = getattr(user, "profile", None)
        if not profile:
            self.message = "Owner profile not found."
            return False

        if not profile.email_verified:
            self.message = "Email verification required. Please complete email OTP verification."
            return False

        if profile.access_status == "SUSPENDED":
            reason = profile.suspension_reason or "Your owner access has been temporarily suspended."
            self.message = f"OWNER_SUSPENDED: {reason}"
            return False

        if profile.access_status == "REVOKED":
            reason = profile.revocation_reason or "Your owner access has been revoked."
            self.message = f"OWNER_REVOKED: {reason}"
            return False

        if profile.approval_status != "APPROVED":
            self.message = f"OWNER_NOT_APPROVED: Your account verification status is '{profile.approval_status}'. Admin approval is required."
            return False

        return True


class IsAdminOrStaffUser(BasePermission):
    """
    Allows access strictly to authenticated administrators and staff members.
    Used for dedicated admin review endpoints and owner access management.
    """
    message = "Administrator privileges required to access this endpoint."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.is_staff or user.is_superuser))
