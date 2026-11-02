from django.urls import path

from .views import (
    AdminVerificationRequestListView,
    AdminVerificationReviewActionView,
    AdminOwnerListView,
    AdminOwnerAccessActionView,
    AdminAuditLogListView,
    OwnerVerificationRequestDetailView,
)

urlpatterns = [
    path("verification-requests/", AdminVerificationRequestListView.as_view(), name="admin-verification-list"),
    path("verification-requests/<int:pk>/", OwnerVerificationRequestDetailView.as_view(), name="admin-verification-detail"),
    path("verification-requests/<int:pk>/review/", AdminVerificationReviewActionView.as_view(), name="admin-verification-review"),
    path("owners/", AdminOwnerListView.as_view(), name="admin-owner-list"),
    path("owners/<int:user_id>/manage-access/", AdminOwnerAccessActionView.as_view(), name="admin-owner-manage-access"),
    path("audit-logs/", AdminAuditLogListView.as_view(), name="admin-audit-logs"),
]
