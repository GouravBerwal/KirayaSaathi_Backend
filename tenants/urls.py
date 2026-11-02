
from django.urls import path
from . import views

urlpatterns = [
    path(
        "",
        views.TenantListCreateAPIView.as_view(),
        name="tenant-list-create",
    ),
    path(
        "rental-agreements/",
        views.RentalAgreementListCreateAPIView.as_view(),
        name="rental-agreement-list-create",
    ),
    path("<int:pk>/", views.TenantDetailAPIView.as_view(), name="tenant-detail"),
    path(
        "rental-agreements/<int:pk>/",
        views.RentalAgreementDetailAPIView.as_view(),
        name="rental-agreement-detail",
    ),
    path(
        "security-deposits/",
        views.SecurityDepositListAPIView.as_view(),
        name="security-deposit-list",
    ),
    path(
        "security-deposits/<int:pk>/",
        views.SecurityDepositDetailAPIView.as_view(),
        name="security-deposit-detail",
    ),

]
