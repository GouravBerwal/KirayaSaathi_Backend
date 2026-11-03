import re
import os
import json
import base64
import logging
import urllib.parse
import urllib.request
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

logger = logging.getLogger(__name__)


def send_fast2sms(phone_raw: str, message: str) -> bool:
    """Send Quick SMS to an Indian 10-digit mobile number via Fast2SMS HTTPS API."""
    api_key = os.getenv("FAST2SMS_API_KEY", getattr(settings, "FAST2SMS_API_KEY", "")).strip()
    if not api_key:
        api_key = getattr(settings, "SMS_API_KEY", "").strip() or os.getenv("SMS_API_KEY", "").strip()
    if not api_key:
        return False

    clean_digits = re.sub(r"\D", "", str(phone_raw))
    if clean_digits.startswith("91") and len(clean_digits) == 12:
        clean_digits = clean_digits[2:]
    elif clean_digits.startswith("0") and len(clean_digits) == 11:
        clean_digits = clean_digits[1:]

    if len(clean_digits) != 10:
        return False

    payload = json.dumps({
        "route": "q",
        "message": message[:160],
        "language": "english",
        "flash": 0,
        "numbers": clean_digits,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://www.fast2sms.com/dev/bulkV2",
        data=payload,
        headers={
            "authorization": api_key,
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
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
            body = resp.read().decode("utf-8", errors="ignore")
            data = json.loads(body) if body else {}
            is_ok = resp.status in (200, 201) and (data.get("return") is True or "request_id" in data)
            if is_ok:
                logger.info("Fast2SMS successfully delivered to %s", clean_digits)
            else:
                logger.warning("Fast2SMS returned non-success: %s", body)
            return is_ok
    except Exception as e:
        logger.warning("Fast2SMS dispatch failed: %s", e)
        return False


def send_twilio_sms(phone_raw: str, message: str) -> bool:
    """Send SMS via Twilio REST API."""
    sid = getattr(settings, "TWILIO_ACCOUNT_SID", "").strip() or os.getenv("TWILIO_ACCOUNT_SID", "").strip()
    token = getattr(settings, "TWILIO_AUTH_TOKEN", "").strip() or os.getenv("TWILIO_AUTH_TOKEN", "").strip()
    from_num = getattr(settings, "TWILIO_PHONE_NUMBER", "").strip() or os.getenv("TWILIO_PHONE_NUMBER", "").strip()
    if not (sid and token and from_num):
        return False

    digits = clean_phone_number(phone_raw)
    to_num = f"+{digits}" if not digits.startswith("+") else digits

    url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
    data = urllib.parse.urlencode({
        "From": from_num,
        "To": to_num,
        "Body": message[:160],
    }).encode("utf-8")

    req = urllib.request.Request(url, data=data, method="POST")
    auth = base64.b64encode(f"{sid}:{token}".encode("ascii")).decode("ascii")
    req.add_header("Authorization", f"Basic {auth}")
    req.add_header("User-Agent", "Mozilla/5.0")
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
        logger.warning("Twilio SMS failed: %s", e)
        return False


def clean_phone_number(phone_raw):
    """Normalize phone to international format (defaulting to India +91 if 10 digits)."""
    if not phone_raw:
        return ""
    digits = re.sub(r"\D", "", str(phone_raw))
    if digits.startswith("0") and len(digits) == 11:
        digits = digits[1:]
    if len(digits) == 10:
        return f"91{digits}"
    if len(digits) == 12 and digits.startswith("91"):
        return digits
    return digits


def get_notification_context(notification):
    """Extract tenant, room, property and owner information from notification."""
    tenant = notification.tenant
    owner = tenant.owner

    property_name = "Property"
    room_number = "N/A"

    if notification.rent_record:
        agreement = notification.rent_record.agreement
        property_name = agreement.room.property.name
        room_number = agreement.room.room_number
    elif notification.electricity_bill:
        room = notification.electricity_bill.meter.room
        property_name = room.property.name
        room_number = room.room_number
    else:
        # Fallback to active agreement of tenant
        active_ag = tenant.agreements.filter(status="ACTIVE").first()
        if active_ag:
            property_name = active_ag.room.property.name
            room_number = active_ag.room.room_number

    owner_name = (
        f"{owner.first_name} {owner.last_name}".strip() or owner.username
        if owner
        else "Property Owner"
    )

    return {
        "tenant_name": tenant.full_name,
        "tenant_phone": tenant.phone,
        "tenant_email": tenant.email,
        "property_name": property_name,
        "room_number": room_number,
        "owner_name": owner_name,
        "amount_due": notification.amount_due,
        "due_date": notification.due_date.strftime("%d %b %Y"),
        "title": notification.title,
    }


def format_notification_text(notification):
    """Generate human-friendly Hindi/English reminder message."""
    ctx = get_notification_context(notification)
    return (
        f"Namaste {ctx['tenant_name']} ji,\n\n"
        f"Yeh KirayaSetu ki taraf se {ctx['title']} ki reminder hai:\n"
        f"• Property: {ctx['property_name']} (Room {ctx['room_number']})\n"
        f"• Pending Amount: Rs. {ctx['amount_due']}\n"
        f"• Due Date: {ctx['due_date']}\n\n"
        f"Kripya samay par bhugtan karein. Payment ke baad Invoice par 'Pay Now' dabakar UPI se pay karein ya UTR share karein.\n\n"
        f"Dhanyawaad,\n"
        f"{ctx['owner_name']}"
    )


def generate_whatsapp_url(notification):
    """Generate instant 1-click WhatsApp deep-link with pre-filled reminder text."""
    ctx = get_notification_context(notification)
    phone = clean_phone_number(ctx["tenant_phone"])
    if not phone:
        return ""
    text = format_notification_text(notification)
    encoded = urllib.parse.quote(text)
    return f"https://wa.me/{phone}?text={encoded}"


def send_actual_notification(notification, channel="WHATSAPP"):
    """
    Dispatch message through actual gateway or return 1-click action link.
    Supports WHATSAPP, SMS, and EMAIL.
    """
    ctx = get_notification_context(notification)
    text = format_notification_text(notification)
    channel = channel.upper()
    now = timezone.now()

    dispatch_result = {
        "success": False,
        "channel": channel,
        "recipient": "",
        "message": "",
        "whatsapp_url": "",
    }

    if channel in ["BOTH", "ALL"]:
        email_sent = False
        whatsapp_sent = False
        wa_url = ""

        # 1. Send Email if email exists
        recipient_email = ctx["tenant_email"]
        if recipient_email:
            try:
                subject = f"Monthly Bill & Rent Due: {notification.title} - {ctx['property_name']}"
                from accounts.services import send_http_email_brevo
                html_body = f"""<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 20px; background-color: #f8fafc; color: #1e293b;">
<div style="max-width: 560px; margin: 0 auto; background: #fff; padding: 24px; border-radius: 8px; border: 1px solid #e2e8f0;">
<h2 style="color: #4f46e5; margin-top: 0;">KirayaSaathi Bill Notice</h2>
<p style="white-space: pre-wrap; font-size: 14px; line-height: 1.6;">{text}</p>
</div></div>"""
                if not send_http_email_brevo(recipient_email, subject, html_body, text):
                    send_mail(
                        subject=subject,
                        message=text,
                        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@kirayasetu.com"),
                        recipient_list=[recipient_email],
                        fail_silently=True,
                    )
                email_sent = True
            except Exception as e:
                logger.warning("Email reminder dispatch failed: %s", e)
                email_sent = False

        # 2. Prepare WhatsApp
        recipient_phone = clean_phone_number(ctx["tenant_phone"])
        if recipient_phone:
            wa_url = generate_whatsapp_url(notification)
            whatsapp_sent = True

        notification.is_sent = True
        notification.sent_at = now
        notification.sent_via = "BOTH"
        notification.delivery_status = "SENT"
        notification.save(update_fields=["is_sent", "sent_at", "sent_via", "delivery_status"])

        dispatch_result["success"] = email_sent or whatsapp_sent
        dispatch_result["email_sent"] = email_sent
        dispatch_result["whatsapp_sent"] = whatsapp_sent
        dispatch_result["recipient"] = f"{recipient_email or 'No Email'} / +{recipient_phone or 'No Phone'}"
        dispatch_result["whatsapp_url"] = wa_url
        dispatch_result["message"] = (
            f"Bill dispatched to {ctx['tenant_name']}: "
            f"{'Email Sent ✓ ' if email_sent else 'No Email '} | "
            f"{'WhatsApp Ready ✓' if whatsapp_sent else 'No Phone'}"
        )

    elif channel == "EMAIL":
        recipient_email = ctx["tenant_email"]
        if not recipient_email:
            raise ValueError(f"Tenant {ctx['tenant_name']} ke paas email address saved nahi hai.")

        subject = f"Payment Reminder: {notification.title} - {ctx['property_name']}"
        from accounts.services import send_http_email_brevo
        html_body = f"""<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 20px; background-color: #f8fafc; color: #1e293b;">
<div style="max-width: 560px; margin: 0 auto; background: #fff; padding: 24px; border-radius: 8px; border: 1px solid #e2e8f0;">
<h2 style="color: #4f46e5; margin-top: 0;">KirayaSaathi Bill Reminder</h2>
<p style="white-space: pre-wrap; font-size: 14px; line-height: 1.6;">{text}</p>
</div></div>"""
        sent_ok = False
        try:
            sent_ok = send_http_email_brevo(recipient_email, subject, html_body, text)
        except Exception as e:
            logger.warning("Brevo email failed: %s", e)
            sent_ok = False

        if not sent_ok:
            send_mail(
                subject=subject,
                message=text,
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@kirayasetu.com"),
                recipient_list=[recipient_email],
                fail_silently=False,
            )

        notification.is_sent = True
        notification.sent_at = now
        notification.sent_via = "EMAIL"
        notification.delivery_status = "SENT"
        notification.save(update_fields=["is_sent", "sent_at", "sent_via", "delivery_status"])

        dispatch_result["success"] = True
        dispatch_result["recipient"] = recipient_email
        dispatch_result["message"] = f"Email successfully sent to {recipient_email}!"

    elif channel == "SMS":
        recipient_phone = clean_phone_number(ctx["tenant_phone"])
        if not recipient_phone:
            raise ValueError(f"Tenant {ctx['tenant_name']} ke paas phone number saved nahi hai.")

        sms_sent = False
        gateway_name = ""

        # 1. Try Fast2SMS first (India Quick SMS route)
        try:
            if send_fast2sms(recipient_phone, text):
                sms_sent = True
                gateway_name = "Fast2SMS"
        except Exception as e:
            logger.warning("Fast2SMS attempt error: %s", e)

        # 2. Fallback to Twilio if Fast2SMS didn't send
        if not sms_sent:
            try:
                if send_twilio_sms(recipient_phone, text):
                    sms_sent = True
                    gateway_name = "Twilio"
            except Exception as e:
                logger.warning("Twilio attempt error: %s", e)

        notification.is_sent = True
        notification.sent_at = now
        notification.sent_via = "SMS"
        notification.delivery_status = "SENT" if sms_sent else "PENDING"
        notification.save(update_fields=["is_sent", "sent_at", "sent_via", "delivery_status"])

        dispatch_result["success"] = True
        dispatch_result["sms_sent"] = sms_sent
        dispatch_result["recipient"] = recipient_phone
        if sms_sent:
            dispatch_result["message"] = f"SMS reminder successfully sent to +{recipient_phone} via {gateway_name}!"
        else:
            dispatch_result["message"] = (
                f"SMS recorded for +{recipient_phone}. "
                f"Real SMS dispatch requires FAST2SMS_API_KEY in Render environment settings."
            )

    else:
        # WHATSAPP (Default)
        recipient_phone = clean_phone_number(ctx["tenant_phone"])
        wa_url = generate_whatsapp_url(notification)

        notification.is_sent = True
        notification.sent_at = now
        notification.sent_via = "WHATSAPP"
        notification.delivery_status = "SENT"
        notification.save(update_fields=["is_sent", "sent_at", "sent_via", "delivery_status"])

        dispatch_result["success"] = True
        dispatch_result["recipient"] = recipient_phone
        dispatch_result["whatsapp_url"] = wa_url
        dispatch_result["message"] = f"WhatsApp reminder ready for {ctx['tenant_name']} (+{recipient_phone})!"

    return dispatch_result
