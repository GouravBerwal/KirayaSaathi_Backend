from rest_framework.authentication import SessionAuthentication


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """
    Session authentication that bypasses CSRF checks for REST API endpoints.
    Since the React frontend (Vercel) and Django backend (Render) operate on
    cross-origin domains, security is strictly enforced via CORS (restricted origins)
    and credentials headers. This prevents false-positive CSRF header mismatches
    caused by Django's automatic CSRF cookie rotation during login.
    """

    def enforce_csrf(self, request):
        return  # Bypass DRF's CSRF enforcement for API requests
