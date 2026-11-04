"""
URL configuration for KirayaSaathi project.
Combines Django REST Framework APIs and integrated web application views.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.http import JsonResponse
from config import web_views

def health_check(request):
    """Health check endpoint for Render / cloud monitoring."""
    return JsonResponse({"status": "ok", "service": "kirayasaathi-api"})

urlpatterns = [
    # Health checks for deployment
    path("api/health/", health_check, name="api-health"),
    path("healthz/", health_check, name="healthz"),

    # Administration
    path("admin/", admin.site.urls),

    # Web Authentication & Public Website
    path("", web_views.home_view, name="home"),
    path("landing/", web_views.home_view, name="landing"),
    path("login/", web_views.login_view, name="login"),
    path("register/", web_views.register_view, name="register"),
    path("logout/", web_views.logout_view, name="logout"),

    # Web Application Views (matching Figma names & templates)
    path("dashboard/", web_views.dashboard, name="dashboard"),
    path("property-list/", web_views.property_list, name="property_list"),
    path("property-detail/", web_views.property_detail, name="property-detail"),
    path("property-detail/<int:pk>/", web_views.property_detail, name="property_detail_id"),
    path("property-detail/<int:pk>/", web_views.property_detail, name="property_detail"),
    path("add-property/", web_views.add_property, name="add-property"),
    path("add_property/", web_views.add_property, name="add_property"),
    path("edit-property/", web_views.edit_property, name="edit_property"),
    path("edit-property/<int:pk>/", web_views.edit_property, name="edit_property_id"),
    path("delete-property/<int:pk>/", web_views.delete_property, name="delete_property"),
    path("property-filter/", web_views.property_filter, name="property_filter"),

    # Rooms
    path("rooms/", web_views.rooms, name="rooms"),
    path("add-room/", web_views.add_room, name="add_room"),
    path("delete-room/<int:pk>/", web_views.delete_room, name="delete_room"),

    # Tenants
    path("tenants/", web_views.tenants, name="tenants"),
    path("add-tenant/", web_views.add_tenant, name="add_tenant"),
    path("tenant-profile/", web_views.tenant_profile, name="tenant_profile"),
    path("tenant-profile/<int:pk>/", web_views.tenant_profile, name="tenant_profile_id"),
    path("tenant-detail/", web_views.tenant_detail, name="tenant_detail"),
    path("tenant-detail/<int:pk>/", web_views.tenant_detail, name="tenant_detail_id"),

    # Rent & Payments
    path("rent-management/", web_views.rent_management, name="rent_management"),
    path("rent-management/generate/", web_views.generate_rent_records_view, name="generate_rent_records"),
    path("rent-management/archive/", web_views.archive_billing_month_web_view, name="archive_billing_month"),
    path("rent-management/archive/<int:pk>/download/", web_views.download_archive_web_view, name="download_archive"),
    path("record-payment/", web_views.record_payment_view, name="record_payment"),

    # Electricity
    path("electricity-bill-list/", web_views.electricity_bill_list, name="electricity_bill_list"),
    path("electricity-bill-form/", web_views.electricity_bill_form, name="electricity_bill_form"),

    # Invoices, Reports, Notifications, Settings
    path("invoice-list/", web_views.invoice_list, name="invoice_list"),
    path("reports/", web_views.reports, name="reports"),
    path("notifications/", web_views.notifications, name="notifications"),
    path("notifications/<int:pk>/read/", web_views.mark_notification_read, name="mark_notification_read"),
    path("notifications/generate/", web_views.generate_notifications_view, name="generate_notifications"),
    path("settings/", web_views.settings_view, name="settings"),
    path("search/", web_views.global_search, name="global_search"),

    # =========================================================================
    # REST API Endpoints (backward-compatible v1 contract)
    # =========================================================================
    path("api/properties/", include("properties.urls")),
    path("api/tenants/", include("tenants.urls")),
    path("api/billing/", include("billing.urls")),
    path("api/electricity/", include("electricity.urls")),
    path("api/payments/", include("payments.urls")),
    path("api/dashboard/", include("dashboard.urls")),
    path("api/notifications/", include("notifications.urls")),
    path("api/auth/", include("accounts.urls")),
    path("api/admin/", include("accounts.admin_urls")),
    path("api/reports/", include("reporting.urls")),
]

# Serve media files in development and production
urlpatterns += [
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
]