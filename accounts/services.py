import hmac
import hashlib
import logging
import os
import json
import urllib.request
import secrets
import string
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import EmailOTPChallenge, OwnerProfile

logger = logging.getLogger(__name__)

OTP_EXPIRY_MINUTES = 10
OTP_RESEND_COOLDOWN_SECONDS = 60
OTP_MAX_ATTEMPTS = 5
HOURLY_EMAIL_SEND_LIMIT = 5
HOURLY_IP_SEND_LIMIT = 15


def generate_secure_otp(length: int = 6) -> str:
    """
    Generate a cryptographically secure, numeric one-time password.
    Never uses insecure pseudo-random generators.
    """
    digits = string.digits
    return "".join(secrets.choice(digits) for _ in range(length))


def hash_otp(email: str, otp: str) -> str:
    """
    Hash the OTP using HMAC-SHA256 keyed with Django's SECRET_KEY.
    Binds the hash to the normalized email to prevent cross-account replay.
    """
    secret = settings.SECRET_KEY.encode("utf-8")
    message = f"{email.strip().lower()}:{otp.strip()}".encode("utf-8")
    return hmac.new(secret, message, hashlib.sha256).hexdigest()


def verify_otp_hash(email: str, otp: str, stored_hash: str) -> bool:
    """
    Constant-time comparison of candidate OTP hash with stored hash.
    Mitigates timing attacks.
    """
    candidate_hash = hash_otp(email, otp)
    return hmac.compare_digest(candidate_hash, stored_hash)


def mask_email(email: str) -> str:
    """
    Mask an email address for display in frontend confirmation views.
    Example: 'alexander@example.com' -> 'a***r@example.com'
    """
    if not email or "@" not in email:
        return email

    local_part, domain = email.strip().lower().split("@", 1)
    if len(local_part) <= 2:
        masked_local = f"{local_part[0]}***"
    else:
        masked_local = f"{local_part[0]}***{local_part[-1]}"

    return f"{masked_local}@{domain}"


def get_remaining_cooldown(email: str) -> int:
    """
    Returns the remaining cooldown time in seconds before a new OTP can be requested.
    Returns 0 if cooldown period has elapsed.
    """
    normalized_email = email.strip().lower()
    last_challenge = (
        EmailOTPChallenge.objects.filter(email__iexact=normalized_email)
        .order_by("-created_at")
        .first()
    )
    if not last_challenge:
        return 0

    elapsed_seconds = (timezone.now() - last_challenge.created_at).total_seconds()
    remaining = int(OTP_RESEND_COOLDOWN_SECONDS - elapsed_seconds)
    return max(0, remaining)


def check_rate_limits(email: str, ip_address: str = None) -> tuple[bool, str]:
    """
    Check hourly sending limits for email and IP address.
    Returns (is_allowed, error_message).
    """
    normalized_email = email.strip().lower()
    one_hour_ago = timezone.now() - timedelta(hours=1)

    email_count = EmailOTPChallenge.objects.filter(
        email__iexact=normalized_email,
        created_at__gte=one_hour_ago,
    ).count()

    if email_count >= HOURLY_EMAIL_SEND_LIMIT:
        return (
            False,
            f"Too many verification requests for this email. Please try again in an hour.",
        )

    if ip_address:
        ip_count = EmailOTPChallenge.objects.filter(
            ip_address=ip_address,
            created_at__gte=one_hour_ago,
        ).count()
        if ip_count >= HOURLY_IP_SEND_LIMIT:
            return (
                False,
                f"Too many verification requests from your network. Please try again later.",
            )

    return True, ""


def render_otp_email_templates(otp: str, username: str = "") -> tuple[str, str]:
    """
    Renders both plain-text and HTML versions of the KirayaSetu verification email.
    Notice: Does NOT log the OTP.
    """
    greeting = f"Hello {username}," if username else "Hello,"

    text_content = f"""{greeting}

Thank you for choosing KirayaSetu — India's Premier Rental Property Management Platform.

Your One-Time Password (OTP) for account verification is:

    {otp}

This code is valid for {OTP_EXPIRY_MINUTES} minutes.

SECURITY NOTICE:
- Do NOT share this code with anyone, including KirayaSetu support.
- If you did not request this registration, please ignore this email.

Best regards,
Team KirayaSetu
https://kirayasetu.com
"""

    html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>KirayaSetu Email Verification</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 24px; color: #1e293b;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width: 560px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1); border: 1px solid #e2e8f0;">
    <!-- Header -->
    <tr>
      <td style="background: linear-gradient(135deg, #4f46e5 0%, #3b82f6 100%); padding: 32px 28px; text-align: center;">
        <h1 style="color: #ffffff; margin: 0; font-size: 26px; font-weight: 700; letter-spacing: -0.5px;">KirayaSetu</h1>
        <p style="color: #e0e7ff; margin: 6px 0 0 0; font-size: 13px; font-weight: 500;">Rental Property Management Platform</p>
      </td>
    </tr>
    <!-- Body -->
    <tr>
      <td style="padding: 32px 28px;">
        <h2 style="margin: 0 0 16px 0; font-size: 18px; font-weight: 600; color: #0f172a;">Verify Your Email Address</h2>
        <p style="margin: 0 0 20px 0; font-size: 14px; line-height: 1.6; color: #475569;">
          {greeting}<br>
          Thank you for signing up as a property owner on KirayaSetu. Use the 6-digit verification code below to verify your email address:
        </p>
        
        <!-- OTP Box -->
        <div style="background-color: #f1f5f9; border: 2px dashed #cbd5e1; border-radius: 8px; padding: 20px; text-align: center; margin: 24px 0;">
          <span style="font-family: 'Courier New', Courier, monospace; font-size: 34px; font-weight: 700; letter-spacing: 8px; color: #1e1b4b; display: inline-block;">{otp}</span>
          <p style="margin: 8px 0 0 0; font-size: 12px; color: #64748b; font-weight: 500;">Valid for {OTP_EXPIRY_MINUTES} minutes</p>
        </div>

        <!-- Security Warning Alert -->
        <div style="background-color: #fffbeb; border-left: 4px solid #f59e0b; padding: 12px 16px; border-radius: 4px; margin: 20px 0;">
          <p style="margin: 0; font-size: 13px; color: #92400e; line-height: 1.5;">
            <strong>Security Warning:</strong> Never share this code with anyone. KirayaSetu staff will never ask for your verification code.
          </p>
        </div>

        <p style="margin: 20px 0 0 0; font-size: 13px; color: #64748b; line-height: 1.5;">
          If you didn't create an account with KirayaSetu, you can safely ignore this email.
        </p>
      </td>
    </tr>
    <!-- Footer -->
    <tr>
      <td style="background-color: #f8fafc; padding: 20px 28px; text-align: center; border-top: 1px solid #e2e8f0;">
        <p style="margin: 0; font-size: 12px; color: #94a3b8;">
          &copy; {timezone.now().year} KirayaSetu. All rights reserved.
        </p>
      </td>
    </tr>
  </table>
</body>
</html>
"""
    return text_content, html_content


def send_http_email_resend(to_email: str, subject: str, html_content: str, text_content: str = "") -> bool:
    api_key = os.getenv("RESEND_API_KEY", getattr(settings, "RESEND_API_KEY", "")).strip()
    if not api_key:
        return False

    from_email = os.getenv(
        "RESEND_FROM_EMAIL",
        os.getenv("DEFAULT_FROM_EMAIL", getattr(settings, "DEFAULT_FROM_EMAIL", "")),
    ).strip()
    if not from_email or "@gmail.com" in from_email.lower():
        from_email = "KirayaSaathi <onboarding@resend.dev>"

    payload = json.dumps({
        "from": from_email,
        "to": [to_email],
        "subject": subject,
        "html": html_content,
        "text": text_content,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        },
    )
    try:
        import ssl
        ctx = None
        if os.path.exists("/etc/ssl/certs/ca-certificates.crt"):
            ctx = ssl.create_default_context(cafile="/etc/ssl/certs/ca-certificates.crt")
        elif os.path.exists("/etc/ssl/cert.pem"):
            ctx = ssl.create_default_context(cafile="/etc/ssl/cert.pem")

        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            return resp.status in (200, 201)
    except Exception as e:
        logger.warning("Resend HTTPS email failed: %s", e)
        return False


def send_http_email_brevo(to_email: str, subject: str, html_content: str, text_content: str = "") -> bool:
    api_key = os.getenv("BREVO_API_KEY", "").strip()
    if not api_key:
        return False

    sender_email = os.getenv("EMAIL_HOST_USER", "kirayasaathi.support@gmail.com").strip()
    payload = json.dumps({
        "sender": {"name": "KirayaSaathi", "email": sender_email},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html_content,
        "textContent": text_content,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.brevo.com/v3/smtp/email",
        data=payload,
        headers={
            "api-key": api_key,
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            return resp.status in (200, 201)
    except Exception as e:
        logger.warning("Brevo HTTPS email failed: %s", e)
        return False


def send_verification_email(email: str, otp: str, username: str = "") -> tuple[bool, str]:
    """
    Sends the OTP verification email using Resend, Brevo HTTPS API, or standard Django SMTP.
    Returns (success: bool, method_or_error: str).
    """
    text_content, html_content = render_otp_email_templates(otp, username)
    subject = "Your KirayaSetu Verification Code"
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "KirayaSaathi <kirayasaathi.support@gmail.com>")

    # 1. Try Resend HTTPS API (Port 443 - never blocked on Render)
    if send_http_email_resend(email, subject, html_content, text_content):
        logger.info("OTP verification email delivered via Resend HTTPS to %s", email)
        return True, "resend"

    # 2. Try Brevo HTTPS API (Port 443 - never blocked on Render)
    if send_http_email_brevo(email, subject, html_content, text_content):
        logger.info("OTP verification email delivered via Brevo HTTPS to %s", email)
        return True, "brevo"

    # 3. Try standard Django send_mail (SMTP)
    try:
        send_mail(
            subject=subject,
            message=text_content,
            html_message=html_content,
            from_email=from_email,
            recipient_list=[email],
            fail_silently=False,
        )
        logger.info("OTP verification email delivered via SMTP to %s", email)
        return True, "smtp"
    except Exception as e:
        logger.warning("SMTP email delivery failed: %s", e)
        if not getattr(settings, "ALLOW_OTP_FALLBACK", True):
            raise
        return False, str(e)


def issue_otp_challenge(
    user,
    email: str,
    ip_address: str = None,
    user_agent: str = "",
) -> tuple[EmailOTPChallenge, str]:
    """
    Invalidates any previous challenges for this email,
    generates a new secure OTP, hashes it, saves challenge, and sends email.
    Returns (challenge, otp).
    """
    normalized_email = email.strip().lower()

    # Invalidate all prior unconsumed challenges for this email
    EmailOTPChallenge.objects.filter(
        email__iexact=normalized_email,
        is_consumed=False,
    ).update(is_consumed=True)

    # Generate 6-digit OTP
    otp = generate_secure_otp(6)
    hashed = hash_otp(normalized_email, otp)
    expires_at = timezone.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)

    challenge = EmailOTPChallenge.objects.create(
        email=normalized_email,
        user=user,
        otp_hash=hashed,
        expires_at=expires_at,
        max_attempts=OTP_MAX_ATTEMPTS,
        ip_address=ip_address,
        user_agent=user_agent[:255] if user_agent else "",
    )

    username = user.username if user else ""
    email_sent, _ = send_verification_email(normalized_email, otp, username=username)
    challenge.email_sent = email_sent
    challenge.raw_otp = otp

    return challenge, otp


def send_owner_approval_email(email: str, username: str, property_name: str = "") -> bool:
    """
    Sends workspace approval email when an admin approves an owner verification request.
    Exact message required:
    'Your KirayaSetu workspace is ready! You can now log in and start using your owner dashboard.'
    """
    subject = "Your KirayaSetu Workspace is Ready! — Account Approved"
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "KirayaSetu <no-reply@kirayasetu.com>")
    greeting = f"Hello {username}," if username else "Hello Property Owner,"
    prop_detail = f" for {property_name}" if property_name else ""

    text_content = f"""{greeting}

Congratulations! Your property verification request{prop_detail} has been approved by our administrative team.

Your KirayaSetu workspace is ready! You can now log in and start using your owner dashboard.

Features unlocked:
- Complete Property, Room & Floor Management
- Automated Tenant Rent Records & Monthly Invoicing
- Sub-meter Electricity Unit Billing & Rate Rules
- Payment Tracking & Historical Financial Ledger
- Automated Rent Reminders via WhatsApp & Email

Login to your dashboard:
https://kirayasetu.com/login

Best regards,
KirayaSetu Administrative Team
"""

    html_content = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Workspace Ready</title></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8fafc; padding: 24px; color: #1e293b;">
  <table width="100%" cellspacing="0" cellpadding="0" style="max-width: 580px; margin: 0 auto; background: #fff; border-radius: 12px; overflow: hidden; border: 1px solid #e2e8f0;">
    <tr>
      <td style="background: linear-gradient(135deg, #035E7B 0%, #00877C 100%); padding: 32px 28px; text-align: center;">
        <h1 style="color: #fff; margin: 0; font-size: 24px; font-weight: 700;">KirayaSetu</h1>
        <p style="color: #e6fffa; margin: 6px 0 0; font-size: 13px;">Property Verification Approved</p>
      </td>
    </tr>
    <tr>
      <td style="padding: 32px 28px;">
        <h2 style="color: #035E7B; margin: 0 0 16px; font-size: 20px;">Your Workspace is Ready!</h2>
        <p style="font-size: 14px; line-height: 1.6; color: #475569;">
          {greeting}<br><br>
          Great news! Your property ownership verification{prop_detail} has been reviewed and <strong>approved</strong> by our administrative team.
        </p>
        <div style="background: #f0fdf4; border-left: 4px solid #16a34a; padding: 16px; border-radius: 6px; margin: 24px 0;">
          <p style="margin: 0; font-size: 15px; font-weight: 600; color: #166534;">
            Your KirayaSetu workspace is ready! You can now log in and start using your owner dashboard.
          </p>
        </div>
        <p style="font-size: 14px; color: #475569;">
          You can now add properties, assign tenants, track utility meters, generate monthly bills, and record rent payments.
        </p>
        <div style="text-align: center; margin: 30px 0;">
          <a href="https://kirayasetu.com/login" style="background: #035E7B; color: #ffffff; text-decoration: none; padding: 12px 28px; border-radius: 8px; font-weight: 600; font-size: 14px; display: inline-block;">
            Access Owner Dashboard
          </a>
        </div>
      </td>
    </tr>
    <tr>
      <td style="background: #f8fafc; padding: 16px 28px; text-align: center; border-top: 1px solid #e2e8f0; font-size: 12px; color: #94a3b8;">
        &copy; {timezone.now().year} KirayaSetu Platform. All rights reserved.
      </td>
    </tr>
  </table>
</body>
</html>"""

    try:
        send_mail(
            subject=subject,
            message=text_content,
            html_message=html_content,
            from_email=from_email,
            recipient_list=[email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send approval email to {email}: {e}")
        return False


def send_owner_rejection_email(email: str, username: str, property_name: str, reason: str) -> bool:
    """
    Sends notification to owner when an account/request is rejected with the administrator's note.
    """
    subject = "Notice: Your KirayaSetu Account has been Rejected"
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "KirayaSetu <no-reply@kirayasetu.com>")
    greeting = f"Hello {username}," if username else "Hello Property Owner,"
    prop_detail = f" for '{property_name}'" if property_name else ""

    text_content = f"""{greeting}

This is to inform you that your KirayaSetu property owner account / verification request{prop_detail} has been rejected by the platform administrator.

Administrator's Note / Reason:
{reason or 'The uploaded documents or registration details did not meet our verification criteria.'}

While rejected, access to the owner dashboard is revoked. If you wish to submit revised verification documents or clarify your details, please log in to your KirayaSetu account.

Best regards,
KirayaSetu Verification Team
https://kirayasetu.com
"""

    try:
        send_mail(
            subject=subject,
            message=text_content,
            from_email=from_email,
            recipient_list=[email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send rejection email to {email}: {e}")
        return False


def send_owner_more_info_email(email: str, username: str, property_name: str, message: str) -> bool:
    """
    Sends request for additional information or corrected documents.
    """
    subject = "Additional Information Required — KirayaSetu Verification"
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "KirayaSetu <no-reply@kirayasetu.com>")
    greeting = f"Hello {username}," if username else "Hello,"

    text_content = f"""{greeting}

Our administrative team requires additional information to complete your property verification request for '{property_name}'.

Administrator's Request:
{message}

Please log in to your account at https://kirayasetu.com to review this request and upload the required documents.

Best regards,
KirayaSetu Verification Team
"""

    try:
        send_mail(
            subject=subject,
            message=text_content,
            from_email=from_email,
            recipient_list=[email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send more info email to {email}: {e}")
        return False


def send_owner_suspension_email(email: str, username: str, reason: str) -> bool:
    """
    Sends notice when an owner's account access is temporarily suspended or put on hold.
    """
    subject = "Notice: Your KirayaSetu Account is On Hold / Suspended"
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "KirayaSetu <no-reply@kirayasetu.com>")
    greeting = f"Hello {username}," if username else "Hello,"

    text_content = f"""{greeting}

This is to inform you that your KirayaSetu owner workspace access has been placed ON HOLD / suspended by an administrator.

Administrator's Note:
{reason or 'Administrative compliance review in progress.'}

While on hold, access to the owner dashboard and property records is temporarily restricted.
To resolve this or review administrative feedback, please log in to your account at https://kirayasetu.com or contact support@kirayasetu.com.

Best regards,
KirayaSetu Compliance Team
https://kirayasetu.com
"""

    try:
        send_mail(
            subject=subject,
            message=text_content,
            from_email=from_email,
            recipient_list=[email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send suspension email to {email}: {e}")
        return False


def send_owner_restoration_email(email: str, username: str) -> bool:
    """
    Sends notice when suspended access is restored.
    """
    subject = "Notice: Your KirayaSetu Owner Access has been Restored"
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "KirayaSetu <no-reply@kirayasetu.com>")
    greeting = f"Hello {username}," if username else "Hello,"

    text_content = f"""{greeting}

Your KirayaSetu owner workspace access has been restored. You can now log in and continue managing your rental properties.

Login to Dashboard:
https://kirayasetu.com/login

Best regards,
Team KirayaSetu
"""

    try:
        send_mail(
            subject=subject,
            message=text_content,
            from_email=from_email,
            recipient_list=[email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send restoration email to {email}: {e}")
        return False


def send_owner_revocation_email(email: str, username: str, reason: str) -> bool:
    """
    Sends notice when access is permanently/administratively revoked.
    """
    subject = "Notice: Your KirayaSetu Owner Authorization has been Revoked"
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "KirayaSetu <no-reply@kirayasetu.com>")
    greeting = f"Hello {username}," if username else "Hello,"

    text_content = f"""{greeting}

This notice confirms that your KirayaSetu owner workspace authorization has been revoked.

Reason:
{reason or 'Administrative policy decision.'}

Your account is no longer authorized to use owner features.
Contact support@kirayasetu.com if you require assistance.

Best regards,
KirayaSetu Security & Administration
"""

    try:
        send_mail(
            subject=subject,
            message=text_content,
            from_email=from_email,
            recipient_list=[email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send revocation email to {email}: {e}")
        return False


def send_verification_request_received_email(email: str, username: str, property_name: str) -> bool:
    """
    Sends confirmation when an owner submits a new property verification request.
    """
    subject = "Verification Request Received — KirayaSetu"
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "KirayaSetu <no-reply@kirayasetu.com>")
    greeting = f"Hello {username}," if username else "Hello,"

    text_content = f"""{greeting}

Thank you for submitting your property ownership verification request for '{property_name}'.

Our administrative verification team has received your documents and will review them shortly.
You can monitor your request status in your KirayaSetu portal.

Best regards,
KirayaSetu Verification Team
"""

    try:
        send_mail(
            subject=subject,
            message=text_content,
            from_email=from_email,
            recipient_list=[email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send request received email to {email}: {e}")
        return False

