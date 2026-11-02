from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from django.urls import reverse

from .models import (
    OwnerProfile,
    EmailOTPChallenge,
    OwnerVerificationRequest,
    OwnerAuditLog,
)
from .services import (
    send_owner_approval_email,
    send_owner_rejection_email,
    send_owner_more_info_email,
    send_owner_suspension_email,
    send_owner_restoration_email,
    send_owner_revocation_email,
)


@admin.register(OwnerProfile)
class OwnerProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user_username",
        "user_email",
        "email_verified",
        "approval_status_badge",
        "access_status_badge",
        "approved_at",
        "created_at",
    )
    list_filter = ("approval_status", "access_status", "email_verified")
    search_fields = (
        "user__username",
        "user__email",
        "user__first_name",
        "user__last_name",
        "suspension_reason",
        "revocation_reason",
    )
    readonly_fields = ("created_at", "updated_at", "approved_at", "approved_by")
    actions = [
        "grant_selected_owners",
        "suspend_selected_owners",
        "reject_selected_owners",
        "restore_selected_owners",
        "revoke_selected_owners",
    ]

    @admin.display(description="Username")
    def user_username(self, obj):
        return obj.user.username

    @admin.display(description="Email")
    def user_email(self, obj):
        return obj.user.email

    @admin.display(description="Approval")
    def approval_status_badge(self, obj):
        colors = {
            "APPROVED": "#16a34a",
            "PENDING": "#d97706",
            "REJECTED": "#dc2626",
            "NEEDS_MORE_INFORMATION": "#2563eb",
            "NOT_SUBMITTED": "#6b7280",
        }
        color = colors.get(obj.approval_status, "#6b7280")
        return format_html(
            '<span style="background:{}; color:#fff; padding:3px 8px; border-radius:4px; font-weight:600; font-size:11px;">{}</span>',
            color,
            obj.get_approval_status_display(),
        )

    @admin.display(description="Access")
    def access_status_badge(self, obj):
        colors = {
            "ACTIVE": "#16a34a",
            "SUSPENDED": "#ea580c",
            "REVOKED": "#991b1b",
        }
        color = colors.get(obj.access_status, "#6b7280")
        return format_html(
            '<span style="background:{}; color:#fff; padding:3px 8px; border-radius:4px; font-weight:600; font-size:11px;">{}</span>',
            color,
            obj.get_access_status_display(),
        )

    @admin.action(description="Grant Approval & Access to selected owners")
    def grant_selected_owners(self, request, queryset):
        for profile in queryset:
            if not profile.email_verified:
                self.message_user(
                    request,
                    f"Skipped {profile.user.username}: Email not verified.",
                    level="warning",
                )
                continue
            is_first = profile.approval_status != "APPROVED"
            profile.approval_status = "APPROVED"
            profile.access_status = "ACTIVE"
            profile.approved_at = timezone.now()
            profile.approved_by = request.user
            profile.save()

            OwnerAuditLog.objects.create(
                owner=profile.user,
                performed_by=request.user,
                action="APPROVED",
                notes="Granted approval via Django Admin action.",
            )

            if is_first:
                send_owner_approval_email(profile.user.email, profile.user.username)
        self.message_user(request, "Selected owners granted approval.")

    @admin.action(description="Suspend Access of selected owners")
    def suspend_selected_owners(self, request, queryset):
        for profile in queryset:
            if profile.user.id == request.user.id or profile.user.is_superuser:
                self.message_user(request, f"Skipped {profile.user.username}: Safety guard.", level="error")
                continue
            profile.access_status = "SUSPENDED"
            profile.suspended_at = timezone.now()
            profile.suspension_reason = "Suspended via Django Admin bulk action."
            profile.save()

            OwnerAuditLog.objects.create(
                owner=profile.user,
                performed_by=request.user,
                action="SUSPENDED",
                notes="Suspended via Django Admin bulk action.",
            )
            send_owner_suspension_email(profile.user.email, profile.user.username, profile.suspension_reason)
        self.message_user(request, "Selected owners suspended.")

    @admin.action(description="Reject selected owners (Revoke access & send email)")
    def reject_selected_owners(self, request, queryset):
        for profile in queryset:
            if profile.user.id == request.user.id or profile.user.is_superuser:
                self.message_user(request, f"Skipped {profile.user.username}: Safety guard.", level="error")
                continue
            reason = "Account rejected via Django Admin action."
            profile.approval_status = "REJECTED"
            profile.access_status = "REVOKED"
            profile.revoked_at = timezone.now()
            profile.rejection_reason = reason
            profile.owner_facing_message = reason
            profile.save()

            profile.user.verification_requests.all().update(
                status="REJECTED",
                reviewed_at=timezone.now(),
                reviewed_by=request.user,
                rejection_reason=reason,
                owner_facing_message=reason,
            )

            OwnerAuditLog.objects.create(
                owner=profile.user,
                performed_by=request.user,
                action="REVOKED",
                notes="Rejected and revoked via Django Admin bulk action.",
            )
            send_owner_rejection_email(profile.user.email, profile.user.username, "", reason)
        self.message_user(request, "Selected owners rejected and access revoked.")

    @admin.action(description="Restore Access of selected owners")
    def restore_selected_owners(self, request, queryset):
        for profile in queryset:
            profile.access_status = "ACTIVE"
            profile.suspended_at = None
            profile.suspension_reason = ""
            profile.save()

            OwnerAuditLog.objects.create(
                owner=profile.user,
                performed_by=request.user,
                action="RESTORED",
                notes="Restored via Django Admin bulk action.",
            )
            send_owner_restoration_email(profile.user.email, profile.user.username)
        self.message_user(request, "Selected owners restored.")

    @admin.action(description="Revoke Access of selected owners")
    def revoke_selected_owners(self, request, queryset):
        for profile in queryset:
            if profile.user.id == request.user.id or profile.user.is_superuser:
                self.message_user(request, f"Skipped {profile.user.username}: Safety guard.", level="error")
                continue
            profile.access_status = "REVOKED"
            profile.revoked_at = timezone.now()
            profile.revocation_reason = "Revoked via Django Admin bulk action."
            profile.save()

            OwnerAuditLog.objects.create(
                owner=profile.user,
                performed_by=request.user,
                action="REVOKED",
                notes="Revoked via Django Admin bulk action.",
            )
            send_owner_revocation_email(profile.user.email, profile.user.username, profile.revocation_reason)
        self.message_user(request, "Selected owners revoked.")


@admin.register(OwnerVerificationRequest)
class OwnerVerificationRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "owner_username",
        "property_name",
        "city",
        "relationship",
        "status_badge",
        "submitted_at",
        "documents_preview",
    )
    list_filter = ("status", "property_type", "relationship", "submitted_at")
    search_fields = (
        "owner__username",
        "owner__email",
        "property_name",
        "address",
        "city",
        "postal_code",
    )
    readonly_fields = ("submitted_at", "reviewed_at", "reviewed_by", "documents_display")
    actions = ["approve_selected_requests", "reject_selected_requests"]

    @admin.display(description="Owner")
    def owner_username(self, obj):
        return f"{obj.owner.username} ({obj.owner.email})"

    @admin.display(description="Status")
    def status_badge(self, obj):
        colors = {
            "APPROVED": "#16a34a",
            "PENDING": "#d97706",
            "REJECTED": "#dc2626",
            "NEEDS_MORE_INFORMATION": "#2563eb",
        }
        color = colors.get(obj.status, "#6b7280")
        return format_html(
            '<span style="background:{}; color:#fff; padding:3px 8px; border-radius:4px; font-weight:600; font-size:11px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    @admin.display(description="Uploaded Documents")
    def documents_preview(self, obj):
        links = []
        if obj.ownership_proof:
            url = reverse("secure-document-download", kwargs={"pk": obj.pk, "doc_type": "ownership_proof"})
            links.append(f'<a href="{url}" target="_blank" style="color:#035E7B; font-weight:600;">[Proof]</a>')
        if obj.utility_bill:
            url = reverse("secure-document-download", kwargs={"pk": obj.pk, "doc_type": "utility_bill"})
            links.append(f'<a href="{url}" target="_blank" style="color:#00877C; font-weight:600;">[Utility]</a>')
        if obj.authorization_letter:
            url = reverse("secure-document-download", kwargs={"pk": obj.pk, "doc_type": "authorization_letter"})
            links.append(f'<a href="{url}" target="_blank" style="color:#d97706; font-weight:600;">[Auth]</a>')
        return format_html(" ".join(links) if links else "None")

    @admin.display(description="Document Links")
    def documents_display(self, obj):
        return self.documents_preview(obj)

    @admin.action(description="Approve selected verification requests")
    def approve_selected_requests(self, request, queryset):
        for req_obj in queryset:
            owner = req_obj.owner
            profile, _ = OwnerProfile.objects.get_or_create(user=owner)
            if not profile.email_verified:
                self.message_user(request, f"Skipped #{req_obj.id}: Owner email not verified.", level="warning")
                continue

            is_first = req_obj.status != "APPROVED"
            req_obj.status = "APPROVED"
            req_obj.reviewed_at = timezone.now()
            req_obj.reviewed_by = request.user
            req_obj.owner_facing_message = "Your property verification request has been approved."
            req_obj.save()

            profile.approval_status = "APPROVED"
            profile.access_status = "ACTIVE"
            profile.approved_at = timezone.now()
            profile.approved_by = request.user
            profile.save()

            OwnerAuditLog.objects.create(
                owner=owner,
                performed_by=request.user,
                action="APPROVED",
                notes=f"Approved verification request #{req_obj.id} for property '{req_obj.property_name}'.",
            )

            if is_first:
                send_owner_approval_email(owner.email, owner.username, req_obj.property_name)

        self.message_user(request, "Selected verification requests approved.")

    @admin.action(description="Reject selected verification requests")
    def reject_selected_requests(self, request, queryset):
        for req_obj in queryset:
            owner = req_obj.owner
            profile, _ = OwnerProfile.objects.get_or_create(user=owner)

            reason = "Documentation did not meet verification criteria."
            req_obj.status = "REJECTED"
            req_obj.reviewed_at = timezone.now()
            req_obj.reviewed_by = request.user
            req_obj.rejection_reason = reason
            req_obj.owner_facing_message = reason
            req_obj.save()

            profile.approval_status = "REJECTED"
            profile.rejection_reason = reason
            profile.save()

            OwnerAuditLog.objects.create(
                owner=owner,
                performed_by=request.user,
                action="REJECTED",
                notes=f"Rejected verification request #{req_obj.id}.",
            )
            send_owner_rejection_email(owner.email, owner.username, req_obj.property_name, reason)

        self.message_user(request, "Selected verification requests rejected.")


@admin.register(OwnerAuditLog)
class OwnerAuditLogAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "action_badge", "owner_username", "performed_by_name", "ip_address")
    list_filter = ("action", "created_at")
    search_fields = ("owner__username", "owner__email", "performed_by__username", "notes")
    readonly_fields = ("owner", "performed_by", "action", "notes", "ip_address", "created_at")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description="Owner")
    def owner_username(self, obj):
        return obj.owner.username

    @admin.display(description="Performed By")
    def performed_by_name(self, obj):
        return obj.performed_by.username if obj.performed_by else "System"

    @admin.display(description="Action")
    def action_badge(self, obj):
        colors = {
            "APPROVED": "#16a34a",
            "REJECTED": "#dc2626",
            "SUSPENDED": "#ea580c",
            "RESTORED": "#16a34a",
            "REVOKED": "#991b1b",
            "REQUEST_SUBMITTED": "#2563eb",
            "MORE_INFO_REQUESTED": "#0284c7",
        }
        color = colors.get(obj.action, "#6b7280")
        return format_html(
            '<span style="background:{}; color:#fff; padding:2px 6px; border-radius:3px; font-weight:600; font-size:10px;">{}</span>',
            color,
            obj.get_action_display(),
        )


@admin.register(EmailOTPChallenge)
class EmailOTPChallengeAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "created_at", "expires_at", "attempts", "is_consumed")
    list_filter = ("is_consumed", "created_at")
    search_fields = ("email",)
    readonly_fields = ("otp_hash", "created_at", "consumed_at")
