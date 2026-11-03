from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.contrib.auth import get_user_model
from rest_framework.authentication import SessionAuthentication

User = get_user_model()
ADMIN_SIGNER_SALT = "kirayasaathi-admin-token"
OWNER_SIGNER_SALT = "kirayasaathi-auth-token"


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """
    Session authentication that:
    1. Supports isolated Admin Token authentication via `X-Admin-Token` header.
       This allows administrators to review & approve requests without ever modifying
       or overwriting the owner's session cookie in the same browser.
    2. Supports Owner Auth Token authentication via `X-Auth-Token` or `Authorization: Bearer <token>`.
       This ensures mobile devices (iOS Safari, Android Chrome) with strict 3rd-party cookie blocking
       remain 100% authenticated.
    3. Falls back to standard Django session authentication (cookies).
    4. Bypasses CSRF checks for cross-origin SPA requests.
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

        # 2. Check for Owner Auth Token (X-Auth-Token or Authorization: Bearer <token>)
        auth_token = request.headers.get("X-Auth-Token") or request.META.get("HTTP_X_AUTH_TOKEN")
        if not auth_token:
            auth_header = request.headers.get("Authorization") or request.META.get("HTTP_AUTHORIZATION")
            if auth_header and auth_header.startswith("Bearer "):
                auth_token = auth_header[7:].strip()

        if auth_token:
            signer = TimestampSigner(salt=OWNER_SIGNER_SALT)
            try:
                data = signer.unsign_object(auth_token, max_age=86400 * 30)  # 30 days valid
                user_id = data.get("user_id")
                user = User.objects.filter(id=user_id, is_active=True).first()
                if user:
                    return (user, None)
            except (BadSignature, SignatureExpired):
                pass

        # 3. Fall back to standard session authentication (cookies)
        return super().authenticate(request)

    def enforce_csrf(self, request):
        return  # Bypass DRF's CSRF enforcement
