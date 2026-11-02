from django.urls import path, include

from .views import (
    CSRFTokenView,
    OwnerLoginView,
    OwnerLogoutView,
    OwnerMeView,
    OwnerRegistrationView,
    ResendEmailOTPView,
    VerifyEmailOTPView,
    OwnerVerificationRequestListCreateView,
    OwnerVerificationRequestDetailView,
    SecureDocumentDownloadView,
    ContactInquiryView,
)

urlpatterns = [
    path("csrf/", CSRFTokenView.as_view(), name="auth-csrf"),
    path("register/", OwnerRegistrationView.as_view(), name="owner-register"),
    path("signup/", OwnerRegistrationView.as_view(), name="owner-signup"),
    path("verify-email-otp/", VerifyEmailOTPView.as_view(), name="verify-email-otp"),
    path("resend-email-otp/", ResendEmailOTPView.as_view(), name="resend-email-otp"),
    path("login/", OwnerLoginView.as_view(), name="owner-login"),
    path("logout/", OwnerLogoutView.as_view(), name="owner-logout"),
    path("me/", OwnerMeView.as_view(), name="owner-me"),
    path("contact/", ContactInquiryView.as_view(), name="contact-inquiry"),

    # Property Ownership Verification
    path("verification-requests/", OwnerVerificationRequestListCreateView.as_view(), name="owner-verification-list-create"),
    path("verification-requests/<int:pk>/", OwnerVerificationRequestDetailView.as_view(), name="owner-verification-detail"),
    path("verification-requests/<int:pk>/document/<str:doc_type>/", SecureDocumentDownloadView.as_view(), name="secure-document-download"),

    # Admin actions also available under /api/auth/admin/
    path("admin/", include("accounts.admin_urls")),
]
