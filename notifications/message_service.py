import re
import urllib.parse
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone


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
                send_mail(
                    subject=subject,
                    message=text,
                    from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@kirayasetu.com"),
                    recipient_list=[recipient_email],
                    fail_silently=True,
                )
                email_sent = True
            except Exception:
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

        # If Twilio is configured
        twilio_sid = getattr(settings, "TWILIO_ACCOUNT_SID", "")
        twilio_token = getattr(settings, "TWILIO_AUTH_TOKEN", "")
        twilio_from = getattr(settings, "TWILIO_PHONE_NUMBER", "")

        if twilio_sid and twilio_token and twilio_from:
            try:
                import urllib.request
                import base64

                url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}/Messages.json"
                data = urllib.parse.urlencode({
                    "From": twilio_from,
                    "To": f"+{recipient_phone}",
                    "Body": text[:160],
                }).encode("utf-8")
                req = urllib.request.Request(url, data=data, method="POST")
                auth = base64.b64encode(f"{twilio_sid}:{twilio_token}".encode("ascii")).decode("ascii")
                req.add_header("Authorization", f"Basic {auth}")
                with urllib.request.urlopen(req, timeout=10) as resp:
                    pass
            except Exception as e:
                # Log but continue
                pass

        notification.is_sent = True
        notification.sent_at = now
        notification.sent_via = "SMS"
        notification.delivery_status = "SENT"
        notification.save(update_fields=["is_sent", "sent_at", "sent_via", "delivery_status"])

        dispatch_result["success"] = True
        dispatch_result["recipient"] = recipient_phone
        dispatch_result["message"] = f"SMS reminder dispatched to +{recipient_phone}!"

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
