
from django.urls import path

from . import views


urlpatterns = [
    # Rent records
    path(
        "",
        views.RentRecordListCreateAPIView.as_view(),
        name="rent-record-list-create",
    ),
    path(
        "<int:pk>/",
        views.RentRecordDetailAPIView.as_view(),
        name="rent-record-detail",
    ),

    # Billing archives
    path(
        "archive/",
        views.BillingArchiveListCreateAPIView.as_view(),
        name="billing-archive-list-create",
    ),
    path(
        "archive/<int:pk>/",
        views.BillingArchiveDetailAPIView.as_view(),
        name="billing-archive-detail",
    ),
    path(
        "archive/<int:pk>/download/",
        views.BillingArchiveDownloadAPIView.as_view(),
        name="billing-archive-download",
    ),

    # Owner QR profiles: list, create
    path(
        "qr/",
        views.OwnerQrConfigListCreateAPIView.as_view(),
        name="owner-qr-list-create",
    ),

    # Owner QR profile: retrieve, update, delete
    path(
        "qr/<int:pk>/",
        views.OwnerQrConfigDetailAPIView.as_view(),
        name="owner-qr-detail",
    ),

    # Tenant QR assignments: list, create, or reassign
    path(
        "tenant-qr-assignments/",
        views.TenantQrAssignmentListCreateAPIView.as_view(),
        name="tenant-qr-assignment-list-create",
    ),

    # Tenant QR assignment: retrieve, update, delete
    path(
        "tenant-qr-assignments/<int:pk>/",
        views.TenantQrAssignmentDetailAPIView.as_view(),
        name="tenant-qr-assignment-detail",
    ),
]
