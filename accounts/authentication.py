from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.contrib.auth import get_user_model
from rest_framework.authentication import SessionAuthentication

User = get_user_model()
ADMIN_SIGNER_SALT = "kirayasaathi-admin-token"


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """
    Session authentication that:
    1. Supports isolated Admin Token authentication via `X-Admin-Token` header.
       This allows administrators to review & approve requests without ever modifying
       or overwriting the owner's session cookie in the same browser.
    2. Falls back to standard Django session authentication.
    3. Bypasses CSRF checks for cross-origin SPA requests.
    """

    def authenticate(self, request):
        # 1. Check for dedicated Admin Token in header first
        admin_token = request.headers.get("X-Admin-Token") or request.META.get("HTTP_X_ADMIN_TOKEN")
        if admin_token:
            signer = TimestampSigner(salt=ADMIN_SIGNER_SALT)
            try:
                data = signer.unsign_object(admin_token, max_age=86400)
                user_id = data.get("user_id")
                user = User.objects.filter(id=user_id, is_active=True).first()
                if user and (user.is_staff or user.is_superuser):
                    return (user, None)
            except (BadSignature, SignatureExpired):
                pass

        # 2. Fall back to standard session authentication (cookies)
        return super().authenticate(request)

    def enforce_csrf(self, request):
        return  # Bypass DRF's CSRF enforcement
