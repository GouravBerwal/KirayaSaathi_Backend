"""
Web views for KirayaSetu web application.
Handles template rendering, forms, database queries, and owner isolation.
"""

from decimal import Decimal
from datetime import date, datetime
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum, Count, Q
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone

from properties.models import Property, Room
from tenants.models import Tenant, RentalAgreement
from billing.models import RentRecord, BillingArchive
from billing.services import generate_monthly_rent_records, archive_billing_month
from electricity.models import ElectricityMeter, MeterReading, ElectricityBill
from electricity.services import generate_electricity_bill
from payments.models import Payment
from payments.services import sync_payment_bills
from notifications.models import Notification
from notifications.services import generate_notifications

User = get_user_model()


def get_common_context(request):
    """Context elements shared across templates: owner name, initials, unread count."""
    if not request.user.is_authenticated:
        return {}
    user = request.user
    name = f"{user.first_name} {user.last_name}".strip() or user.username
    initials = "".join([part[0].upper() for part in name.split()[:2]]) or user.username[:2].upper()
    unread_count = Notification.objects.filter(tenant__owner=user, is_read=False).count()
    properties = Property.objects.filter(owner=user).order_by("name")
    current_workspace = properties.first().name if properties.exists() else f"{name}'s Properties"
    return {
        "current_user_name": name,
        "current_user_initials": initials,
        "unread_notifications_count": unread_count,
        "user_properties": properties,
        "current_workspace_name": current_workspace,
        "today": timezone.localdate(),
    }


# ==============================================================================
# AUTHENTICATION & PUBLIC LANDING VIEWS
# ==============================================================================

def home_view(request):
    """
    Public marketing & landing website view (combined from untitled folder).
    Displays Hero, Features, About, Calculator, Demo, Pricing, and Contact.
    If an owner is already logged in, redirects them directly to the dashboard.
    """
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "landing.html", {
        "year": timezone.now().year,
    })


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    next_url = request.GET.get("next") or request.POST.get("next") or reverse("dashboard")
    error = None

    if request.method == "POST":
        identifier = (request.POST.get("identifier") or request.POST.get("username") or "").strip()
        password = request.POST.get("password", "")

        user = None
        if "@" in identifier:
            matching_users = User.objects.filter(email__iexact=identifier)
            if matching_users.count() == 1:
                user = matching_users.first()
        else:
            user = User.objects.filter(username=identifier).first()

        if user:
            auth_user = authenticate(request, username=user.username, password=password)
            if auth_user:
                login(request, auth_user)
                messages.success(request, f"Welcome back, {auth_user.username}!")
                return HttpResponseRedirect(next_url)

        error = "Invalid username/email or password."

    return render(request, "auth/login.html", {
        "next": next_url,
        "error": error,
        "identifier": request.POST.get("identifier", ""),
    })


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    error = None
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")

        if not username or not email or not password:
            error = "All fields are required."
        elif password != confirm_password:
            error = "Passwords do not match."
        elif len(password) < 8:
            error = "Password must be at least 8 characters long."
        elif User.objects.filter(username__iexact=username).exists():
            error = "This username is already taken."
        elif User.objects.filter(email__iexact=email).exists():
            error = "This email is already registered."
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            login(request, user)
            messages.success(request, "Account created successfully! Welcome to KirayaSetu.")
            return redirect("dashboard")

    return render(request, "auth/register.html", {
        "error": error,
        "username": request.POST.get("username", ""),
        "email": request.POST.get("email", ""),
    })


def logout_view(request):
    logout(request)
    messages.info(request, "You have been signed out.")
    return redirect("login")


# ==============================================================================
# DASHBOARD VIEW
# ==============================================================================

@login_required
def dashboard(request):
    owner = request.user
    ctx = get_common_context(request)

    properties = Property.objects.filter(owner=owner)
    rooms = Room.objects.filter(property__owner=owner)
    agreements = RentalAgreement.objects.filter(
        room__property__owner=owner,
        tenant__owner=owner,
    )
    rent_records = RentRecord.objects.filter(
        agreement__room__property__owner=owner,
        agreement__tenant__owner=owner,
    )
    electricity_bills = ElectricityBill.objects.filter(
        meter__room__property__owner=owner
    )
    payments = Payment.objects.filter(
        agreement__room__property__owner=owner
    )

    total_properties = properties.count()
    total_rooms = rooms.count()
    occupied_rooms = rooms.filter(status="OCCUPIED").count()
    vacant_rooms = rooms.filter(status="VACANT").count()
    maintenance_rooms = rooms.filter(status="MAINTENANCE").count()
    occupancy_rate = round((occupied_rooms / total_rooms * 100), 1) if total_rooms > 0 else 0

    active_agreements = agreements.filter(status="ACTIVE")
    active_tenants = active_agreements.values("tenant_id").distinct().count()

    today = timezone.localdate()
    current_month_start = today.replace(day=1)

    # Current month rent stats
    current_month_rent = rent_records.filter(billing_month__year=today.year, billing_month__month=today.month)
    if not current_month_rent.exists():
        current_month_rent = rent_records

    total_rent_billed = current_month_rent.aggregate(total=Sum("rent_amount"))["total"] or Decimal("0.00")
    total_rent_collected = current_month_rent.aggregate(paid=Sum("amount_paid"))["paid"] or Decimal("0.00")
    pending_rent = max(Decimal("0.00"), total_rent_billed - total_rent_collected)

    # Overdue stats across all rent records
    overdue_records = rent_records.filter(due_date__lt=today).exclude(status="PAID")
    overdue_amount = Decimal("0.00")
    for r in overdue_records:
        overdue_amount += max(Decimal("0.00"), r.rent_amount - r.amount_paid)

    # Electricity stats
    total_elec_billed = electricity_bills.aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00")
    total_elec_paid = electricity_bills.aggregate(paid=Sum("amount_paid"))["paid"] or Decimal("0.00")
    pending_elec = max(Decimal("0.00"), total_elec_billed - total_elec_paid)

    # Total collected all time
    completed_payments = payments.filter(status="COMPLETED")
    total_lifetime_collected = completed_payments.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

    # Recent payments
    recent_payments = payments.select_related(
        "agreement__tenant", "rent_record", "electricity_bill"
    ).order_by("-payment_date", "-pk")[:5]

    recent_payment_list = []
    for p in recent_payments:
        bill_desc = "Rent" if p.rent_record_id else ("Electricity" if p.electricity_bill_id else "General")
        recent_payment_list.append({
            "id": p.pk,
            "tenant_name": p.agreement.tenant.full_name,
            "amount": p.amount,
            "payment_date": p.payment_date,
            "payment_method": p.get_payment_method_display(),
            "bill_desc": bill_desc,
            "status": p.status,
            "ref": p.transaction_reference or f"TXN-{p.pk:05d}",
        })

    ctx.update({
        "total_properties": total_properties,
        "total_rooms": total_rooms,
        "occupied_rooms": occupied_rooms,
        "vacant_rooms": vacant_rooms,
        "maintenance_rooms": maintenance_rooms,
        "occupancy_rate": occupancy_rate,
        "active_tenants": active_tenants,
        "total_rent_billed": total_rent_billed,
        "total_rent_collected": total_rent_collected,
        "pending_rent": pending_rent,
        "overdue_amount": overdue_amount,
        "overdue_count": overdue_records.count(),
        "total_elec_billed": total_elec_billed,
        "total_elec_paid": total_elec_paid,
        "pending_elec": pending_elec,
        "total_lifetime_collected": total_lifetime_collected,
        "recent_payments": recent_payment_list,
        "current_date_display": today.strftime("%d %B %Y"),
        "current_month_display": today.strftime("%B %Y"),
    })
    return render(request, "dashboard.html", ctx)


# ==============================================================================
# PROPERTIES VIEWS
# ==============================================================================

@login_required
def property_list(request):
    owner = request.user
    ctx = get_common_context(request)

    query = request.GET.get("q", "").strip()
    properties = Property.objects.filter(owner=owner)
    if query:
        properties = properties.filter(
            Q(name__icontains=query) | Q(address__icontains=query) | Q(city__icontains=query)
        )
    properties = properties.order_by("-id")

    property_items = []
    for prop in properties:
        p_rooms = Room.objects.filter(property=prop)
        total_p_rooms = p_rooms.count()
        occupied_p_rooms = p_rooms.filter(status="OCCUPIED").count()
        vacant_p_rooms = p_rooms.filter(status="VACANT").count()
        property_items.append({
            "obj": prop,
            "total_rooms": total_p_rooms,
            "occupied_rooms": occupied_p_rooms,
            "vacant_rooms": vacant_p_rooms,
            "occupancy_percent": round(occupied_p_rooms / total_p_rooms * 100) if total_p_rooms > 0 else 0,
        })

    ctx.update({
        "properties": property_items,
        "total_properties_count": Property.objects.filter(owner=owner).count(),
        "total_rooms_count": Room.objects.filter(property__owner=owner).count(),
        "search_query": query,
    })
    return render(request, "properties/property_list.html", ctx)


@login_required
def property_detail(request, pk=None):
    owner = request.user
    ctx = get_common_context(request)

    if pk:
        prop = get_object_or_404(Property, pk=pk, owner=owner)
    else:
        prop = Property.objects.filter(owner=owner).first()
        if not prop:
            messages.info(request, "Please add your first property.")
            return redirect("add-property")

    rooms = Room.objects.filter(property=prop).order_by("room_number")
    total_rooms = rooms.count()
    occupied_rooms = rooms.filter(status="OCCUPIED").count()
    vacant_rooms = rooms.filter(status="VACANT").count()

    # Active agreements and tenants
    room_details = []
    for r in rooms:
        ag = RentalAgreement.objects.filter(room=r, status="ACTIVE").select_related("tenant").first()
        room_details.append({
            "room": r,
            "agreement": ag,
            "tenant": ag.tenant if ag else None,
        })

    # Financial metrics for this property
    expected_rent = sum(
        (item["agreement"].monthly_rent if item["agreement"] else item["room"].monthly_rent or prop.monthly_rent)
        for item in room_details
        if item["room"].status == "OCCUPIED"
    )

    prop_rent_records = RentRecord.objects.filter(
        agreement__room__property=prop,
        agreement__tenant__owner=owner,
    )
    collected_rent = prop_rent_records.aggregate(total=Sum("amount_paid"))["total"] or Decimal("0.00")
    total_rent_due = prop_rent_records.aggregate(total=Sum("rent_amount"))["total"] or Decimal("0.00")
    outstanding_rent = max(Decimal("0.00"), total_rent_due - collected_rent)

    ctx.update({
        "property": prop,
        "rooms": room_details,
        "total_rooms": total_rooms,
        "occupied_rooms": occupied_rooms,
        "vacant_rooms": vacant_rooms,
        "occupancy_rate": round(occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0,
        "expected_rent": expected_rent,
        "collected_rent": collected_rent,
        "outstanding_rent": outstanding_rent,
    })
    return render(request, "properties/property_detail.html", ctx)


@login_required
def add_property(request):
    ctx = get_common_context(request)

    if request.method == "POST":
        name = request.POST.get("property_name") or request.POST.get("name")
        property_type = request.POST.get("property_type", "BUILDING").upper()
        if property_type in ["RESIDENTIAL", "COMMERCIAL", "INDEPENDENT"]:
            property_type = "BUILDING"
        elif property_type == "PG":
            property_type = "HOSTEL"

        valid_types = [t[0] for t in Property.PROPERTY_TYPES]
        if property_type not in valid_types:
            property_type = "BUILDING"

        address = request.POST.get("street_address") or request.POST.get("address", "")
        city = request.POST.get("city", "Bengaluru")
        state = request.POST.get("state", "Karnataka")
        pin_code = request.POST.get("pin_code", "560102")

        monthly_rent = request.POST.get("monthly_rent") or "0"
        security_deposit = request.POST.get("security_deposit") or "0"
        rent_due_day = request.POST.get("rent_due_day") or "5"
        electricity_rate = request.POST.get("electricity_rate") or "0"

        try:
            prop = Property.objects.create(
                owner=request.user,
                name=name,
                property_type=property_type,
                address=address,
                city=city,
                state=state,
                pin_code=pin_code,
                monthly_rent=Decimal(monthly_rent),
                security_deposit=Decimal(security_deposit),
                rent_due_day=int(rent_due_day),
                electricity_rate=Decimal(electricity_rate),
            )
            messages.success(request, f"Property '{prop.name}' created successfully!")
            return redirect("property_list")
        except Exception as e:
            messages.error(request, f"Error creating property: {e}")

    return render(request, "properties/add_property.html", ctx)


@login_required
def edit_property(request, pk=None):
    owner = request.user
    ctx = get_common_context(request)

    if pk:
        prop = get_object_or_404(Property, pk=pk, owner=owner)
    else:
        prop = Property.objects.filter(owner=owner).first()
        if not prop:
            return redirect("add-property")

    if request.method == "POST":
        prop.name = request.POST.get("property_name") or request.POST.get("name") or prop.name
        prop.address = request.POST.get("street_address") or request.POST.get("address") or prop.address
        prop.city = request.POST.get("city") or prop.city
        prop.state = request.POST.get("state") or prop.state
        prop.pin_code = request.POST.get("pin_code") or prop.pin_code
        prop.monthly_rent = Decimal(request.POST.get("monthly_rent") or prop.monthly_rent)
        prop.security_deposit = Decimal(request.POST.get("security_deposit") or prop.security_deposit)
        prop.rent_due_day = int(request.POST.get("rent_due_day") or prop.rent_due_day)
        prop.electricity_rate = Decimal(request.POST.get("electricity_rate") or prop.electricity_rate)
        prop.save()
        messages.success(request, f"Property '{prop.name}' updated successfully!")
        return redirect("property_detail", pk=prop.pk)

    ctx["property"] = prop
    return render(request, "properties/edit_property.html", ctx)


@login_required
def delete_property(request, pk):
    if request.method == "POST":
        prop = get_object_or_404(Property, pk=pk, owner=request.user)
        try:
            prop.delete()
            messages.success(request, f"Property '{prop.name}' deleted successfully.")
        except Exception as e:
            messages.error(request, f"Cannot delete property: {e}")
    return redirect("property_list")


@login_required
def property_filter(request):
    return property_list(request)


# ==============================================================================
# ROOMS VIEWS
# ==============================================================================

@login_required
def rooms(request):
    owner = request.user
    ctx = get_common_context(request)

    status_filter = request.GET.get("status", "").upper()
    property_filter_id = request.GET.get("property_id")
    search_q = request.GET.get("q", "").strip()

    all_rooms = Room.objects.filter(property__owner=owner).select_related("property").order_by("room_number")

    total_count = all_rooms.count()
    occupied_count = all_rooms.filter(status="OCCUPIED").count()
    vacant_count = all_rooms.filter(status="VACANT").count()
    avg_rent = all_rooms.aggregate(avg=Sum("monthly_rent"))["avg"]
    avg_rent_val = round(avg_rent / total_count, 2) if total_count > 0 and avg_rent else Decimal("0.00")

    filtered_rooms = all_rooms
    if status_filter in ["OCCUPIED", "VACANT", "MAINTENANCE"]:
        filtered_rooms = filtered_rooms.filter(status=status_filter)
    if property_filter_id:
        filtered_rooms = filtered_rooms.filter(property_id=property_filter_id)
    if search_q:
        filtered_rooms = filtered_rooms.filter(
            Q(room_number__icontains=search_q) | Q(property__name__icontains=search_q)
        )

    room_items = []
    for r in filtered_rooms:
        all_ags = list(RentalAgreement.objects.filter(room=r, status="ACTIVE").select_related("tenant"))
        primary_ag = all_ags[0] if all_ags else None
        room_items.append({
            "room": r,
            "agreement": primary_ag,
            "tenant": primary_ag.tenant if primary_ag else None,
            "tenants": [ag.tenant for ag in all_ags],
            "agreements": all_ags,
            "occupied_beds": len(all_ags),
            "capacity": r.capacity,
            "vacant_beds": max(0, r.capacity - len(all_ags)),
            "is_full": len(all_ags) >= r.capacity,
        })

    ctx.update({
        "rooms": room_items,
        "total_rooms": total_count,
        "occupied_rooms": occupied_count,
        "vacant_rooms": vacant_count,
        "avg_rent": avg_rent_val,
        "status_filter": status_filter,
        "search_query": search_q,
    })
    return render(request, "rooms/rooms.html", ctx)


@login_required
def add_room(request):
    owner = request.user
    ctx = get_common_context(request)
    properties = Property.objects.filter(owner=owner)

    if not properties.exists():
        messages.warning(request, "You must create a property before adding rooms.")
        return redirect("add-property")

    if request.method == "POST":
        property_id = request.POST.get("property_id")
        prop = get_object_or_404(Property, pk=property_id, owner=owner)
        room_number = request.POST.get("room_number", "").strip()
        floor = request.POST.get("floor", "First floor").strip()
        room_type = request.POST.get("room_type", "SINGLE").upper()
        monthly_rent = request.POST.get("monthly_rent") or prop.monthly_rent
        security_deposit = request.POST.get("security_deposit") or prop.security_deposit
        status_val = request.POST.get("status", "VACANT").upper()

        if Room.objects.filter(property=prop, room_number=room_number).exists():
            messages.error(request, f"Room {room_number} already exists in {prop.name}.")
        else:
            try:
                room = Room.objects.create(
                    property=prop,
                    room_number=room_number,
                    floor=floor,
                    room_type=room_type,
                    monthly_rent=Decimal(monthly_rent),
                    security_deposit=Decimal(security_deposit),
                    status=status_val,
                )
                messages.success(request, f"Room '{room.room_number}' added successfully to {prop.name}!")
                return redirect("rooms")
            except Exception as e:
                messages.error(request, f"Error creating room: {e}")

    ctx["properties"] = properties
    return render(request, "rooms/add_room.html", ctx)


@login_required
def delete_room(request, pk):
    if request.method == "POST":
        room = get_object_or_404(Room, pk=pk, property__owner=request.user)
        try:
            room.delete()
            messages.success(request, f"Room {room.room_number} deleted successfully.")
        except Exception as e:
            messages.error(request, f"Cannot delete room: {e}")
    return redirect("rooms")


# ==============================================================================
# TENANTS VIEWS
# ==============================================================================

@login_required
def tenants(request):
    owner = request.user
    ctx = get_common_context(request)

    search_q = request.GET.get("q", "").strip()
    tenant_qs = Tenant.objects.filter(owner=owner).order_by("-id")
    if search_q:
        tenant_qs = tenant_qs.filter(
            Q(full_name__icontains=search_q) | Q(email__icontains=search_q) | Q(phone__icontains=search_q)
        )

    tenant_list = []
    total_deposits = Decimal("0.00")
    for t in tenant_qs:
        active_ag = RentalAgreement.objects.filter(tenant=t, status="ACTIVE").select_related("room__property").first()
        if active_ag:
            total_deposits += active_ag.security_deposit
        tenant_list.append({
            "tenant": t,
            "agreement": active_ag,
            "room": active_ag.room if active_ag else None,
            "property": active_ag.room.property if active_ag else None,
        })

    ctx.update({
        "tenants": tenant_list,
        "total_tenants": tenant_qs.count(),
        "active_tenants_count": len([item for item in tenant_list if item["agreement"]]),
        "total_deposits": total_deposits,
        "search_query": search_q,
    })
    return render(request, "tenants/tenants.html", ctx)


@login_required
def tenant_detail(request, pk=None):
    owner = request.user
    ctx = get_common_context(request)

    if pk:
        tenant = get_object_or_404(Tenant, pk=pk, owner=owner)
    else:
        tenant = Tenant.objects.filter(owner=owner).first()
        if not tenant:
            messages.info(request, "No tenants found. Add your first tenant.")
            return redirect("tenants")

    agreements = RentalAgreement.objects.filter(tenant=tenant).select_related("room__property").order_by("-start_date")
    active_ag = agreements.filter(status="ACTIVE").first()

    if request.method == "POST":
        tenant.full_name = request.POST.get("full_name", tenant.full_name).strip()
        tenant.email = request.POST.get("email", tenant.email).strip()
        tenant.phone = request.POST.get("phone", tenant.phone).strip()
        tenant.emergency_contact_name = request.POST.get("emergency_contact_name", tenant.emergency_contact_name).strip()
        tenant.emergency_contact_phone = request.POST.get("emergency_contact_phone", tenant.emergency_contact_phone).strip()
        tenant.save()

        # Handle room change if submitted
        new_room_id = request.POST.get("room_id")
        if new_room_id and (not active_ag or str(active_ag.room_id) != str(new_room_id)):
            new_room = get_object_or_404(Room, pk=new_room_id, property__owner=owner)
            with transaction.atomic():
                if active_ag:
                    active_ag.status = "TERMINATED"
                    active_ag.end_date = timezone.localdate()
                    active_ag.save(update_fields=["status", "end_date"])
                    active_ag.room.status = "VACANT"
                    active_ag.room.save(update_fields=["status"])

                RentalAgreement.objects.create(
                    tenant=tenant,
                    room=new_room,
                    start_date=timezone.localdate(),
                    monthly_rent=new_room.monthly_rent,
                    security_deposit=new_room.security_deposit,
                    status="ACTIVE",
                )
                new_room.status = "OCCUPIED"
                new_room.save(update_fields=["status"])

        messages.success(request, f"Tenant '{tenant.full_name}' updated successfully.")
        return redirect("tenant_profile_id", pk=tenant.id)

    all_owner_rooms = Room.objects.filter(property__owner=owner).exclude(status="MAINTENANCE")
    available_rooms = [
        r for r in all_owner_rooms
        if r.status == "VACANT" or r.rental_agreements.filter(status="ACTIVE").count() < r.capacity
    ]
    ctx.update({
        "tenant": tenant,
        "active_agreement": active_ag,
        "agreements": agreements,
        "available_rooms": available_rooms,
    })
    return render(request, "tenants/tenant_detail.html", ctx)


@login_required
def tenant_profile(request, pk=None):
    owner = request.user
    ctx = get_common_context(request)

    if pk:
        tenant = get_object_or_404(Tenant, pk=pk, owner=owner)
    else:
        tenant = Tenant.objects.filter(owner=owner).first()
        if not tenant:
            messages.info(request, "No tenants found. Add your first tenant.")
            return redirect("tenants")

    agreements = RentalAgreement.objects.filter(tenant=tenant).select_related("room__property").order_by("-start_date")
    active_ag = agreements.filter(status="ACTIVE").first()

    rent_records = RentRecord.objects.filter(agreement__tenant=tenant).order_by("-billing_month")
    payments = Payment.objects.filter(agreement__tenant=tenant).order_by("-payment_date")[:15]

    monthly_rent = active_ag.monthly_rent if active_ag else Decimal("0.00")
    security_deposit = active_ag.security_deposit if active_ag else Decimal("0.00")

    total_rent_due = rent_records.aggregate(total=Sum("rent_amount"))["total"] or Decimal("0.00")
    total_rent_paid = rent_records.aggregate(total=Sum("amount_paid"))["total"] or Decimal("0.00")
    outstanding_balance = max(Decimal("0.00"), total_rent_due - total_rent_paid)

    ctx.update({
        "tenant": tenant,
        "active_agreement": active_ag,
        "agreements": agreements,
        "rent_records": rent_records,
        "payments": payments,
        "monthly_rent": monthly_rent,
        "security_deposit": security_deposit,
        "outstanding_balance": outstanding_balance,
    })
    return render(request, "tenants/tenant_profile.html", ctx)


@login_required
def add_tenant(request):
    owner = request.user
    ctx = get_common_context(request)

    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        emergency_contact = request.POST.get("emergency_contact", "").strip()
        emergency_phone = request.POST.get("emergency_phone", "").strip()
        room_id = request.POST.get("room_id")

        if not full_name or not phone:
            messages.error(request, "Tenant name and phone are required.")
        else:
            with transaction.atomic():
                tenant = Tenant.objects.create(
                    owner=owner,
                    full_name=full_name,
                    email=email,
                    phone=phone,
                    emergency_contact_name=emergency_contact,
                    emergency_contact_phone=emergency_phone,
                )

                if room_id:
                    room = get_object_or_404(Room, pk=room_id, property__owner=owner)
                    RentalAgreement.objects.create(
                        tenant=tenant,
                        room=room,
                        start_date=timezone.localdate(),
                        monthly_rent=room.monthly_rent,
                        security_deposit=room.security_deposit,
                        status="ACTIVE",
                    )
                    room.status = "OCCUPIED"
                    room.save(update_fields=["status"])

                messages.success(request, f"Tenant '{tenant.full_name}' added successfully!")
                return redirect("tenants")

    all_rooms = Room.objects.filter(property__owner=owner).exclude(status="MAINTENANCE").select_related("property")
    vacant_rooms = [
        r for r in all_rooms
        if r.status == "VACANT" or r.rental_agreements.filter(status="ACTIVE").count() < r.capacity
    ]
    ctx["vacant_rooms"] = vacant_rooms
    return render(request, "tenants/tenant_detail.html", ctx)


# ==============================================================================
# RENT MANAGEMENT & PAYMENTS VIEWS
# ==============================================================================

@login_required
def rent_management(request):
    owner = request.user
    ctx = get_common_context(request)

    records = RentRecord.objects.filter(
        agreement__room__property__owner=owner,
        agreement__tenant__owner=owner,
    ).select_related("agreement__tenant", "agreement__room__property").order_by("-billing_month")

    archives = BillingArchive.objects.filter(owner=owner).order_by("-billing_month")

    status_filter = request.GET.get("status", "").upper()
    if status_filter in ["PENDING", "PAID", "PARTIAL", "OVERDUE"]:
        records = records.filter(status=status_filter)

    total_billed = Decimal("0.00")
    total_paid = Decimal("0.00")
    pending_total = Decimal("0.00")
    for r in records:
        total_billed += r.rent_amount
        total_paid += r.amount_paid
        pending_total += max(Decimal("0.00"), r.rent_amount - r.amount_paid)

    ctx.update({
        "rent_records": records,
        "archives": archives,
        "total_billed": total_billed,
        "total_paid": total_paid,
        "pending_total": pending_total,
        "status_filter": status_filter,
    })
    return render(request, "rent/rent_management.html", ctx)


@login_required
def archive_billing_month_web_view(request):
    if request.method == "POST":
        owner = request.user
        billing_month = request.POST.get("billing_month")
        property_id = request.POST.get("property_id") or None
        notes = request.POST.get("notes", "").strip()
        if billing_month:
            try:
                res = archive_billing_month(
                    owner=owner,
                    billing_month=billing_month,
                    property_id=property_id,
                    notes=notes,
                )
                messages.success(
                    request,
                    f"Successfully archived {res['archive'].billing_month.strftime('%B %Y')}! "
                    f"{res['meters_rolled_over']} electricity meters rolled over for next month."
                )
            except Exception as e:
                messages.error(request, f"Failed to archive month: {e}")
        else:
            messages.error(request, "Billing month is required for archiving.")
    return redirect("rent_management")


@login_required
def download_archive_web_view(request, pk):
    owner = request.user
    archive = get_object_or_404(BillingArchive, pk=pk, owner=owner)
    import csv
    from django.http import HttpResponse

    month_label = archive.billing_month.strftime("%B_%Y")
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="Billing_Archive_{month_label}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "Tenant Name", "Phone", "Property", "Room", "Billing Month", "Due Date",
        "Room Rent (INR)", "Rent Paid (INR)", "Rent Balance (INR)", "Rent Status",
        "Meter No.", "Previous Reading", "Current Reading", "Units Consumed",
        "Rate / Unit", "Electricity Amt (INR)", "Electricity Paid (INR)", "Electricity Status",
        "Total Billed (INR)", "Total Paid (INR)", "Final Balance (INR)"
    ])

    for item in archive.snapshot_data:
        writer.writerow([
            item.get("tenant_name", ""),
            item.get("tenant_phone", ""),
            item.get("property_name", ""),
            item.get("room_number", ""),
            item.get("billing_month", ""),
            item.get("due_date", ""),
            item.get("rent_amount", "0"),
            item.get("rent_paid", "0"),
            item.get("rent_balance", "0"),
            item.get("rent_status", ""),
            item.get("meter_number", ""),
            item.get("previous_reading", "0"),
            item.get("current_reading", "0"),
            item.get("units_consumed", "0"),
            item.get("rate_per_unit", "0"),
            item.get("electricity_amount", "0"),
            item.get("electricity_paid", "0"),
            item.get("electricity_status", ""),
            item.get("total_billed", "0"),
            item.get("total_paid", "0"),
            item.get("balance", "0"),
        ])

    return response


@login_required
def generate_rent_records_view(request):
    if request.method == "POST":
        today = timezone.localdate()
        first_of_month = today.replace(day=1)
        created_count = generate_monthly_rent_records(first_of_month)
        messages.success(request, f"Generated {created_count} rent records for {today.strftime('%B %Y')}.")
    return redirect("rent_management")


@login_required
def record_payment_view(request):
    if request.method == "POST":
        owner = request.user
        bill_type = request.POST.get("bill_type", "RENT")
        bill_id = request.POST.get("bill_id") or request.POST.get("record_id")
        agreement_id = request.POST.get("agreement_id")
        amount = Decimal(request.POST.get("amount", "0"))
        method = request.POST.get("payment_method", "UPI")
        ref = request.POST.get("transaction_reference", "").strip()

        rent_record = None
        electricity_bill = None
        agreement = None

        if bill_type == "RENT":
            if bill_id:
                rent_record = get_object_or_404(
                    RentRecord, pk=bill_id, agreement__room__property__owner=owner
                )
                agreement = rent_record.agreement
            elif agreement_id:
                agreement = get_object_or_404(
                    RentalAgreement, pk=agreement_id, room__property__owner=owner
                )
                rent_record = RentRecord.objects.filter(
                    agreement=agreement, status__in=["PENDING", "PARTIAL"]
                ).order_by("-billing_month").first()
        elif bill_type == "ELECTRICITY":
            electricity_bill = get_object_or_404(
                ElectricityBill, pk=bill_id, meter__room__property__owner=owner
            )
            agreement = RentalAgreement.objects.filter(
                room=electricity_bill.meter.room, status="ACTIVE"
            ).first()

        if agreement and amount > 0:
            try:
                with transaction.atomic():
                    payment = Payment.objects.create(
                        agreement=agreement,
                        amount=amount,
                        payment_date=timezone.now(),
                        payment_method=method,
                        status="COMPLETED",
                        rent_record=rent_record,
                        electricity_bill=electricity_bill,
                        transaction_reference=ref,
                    )
                    if rent_record:
                        sync_payment_bills(rent_record_ids=[rent_record.pk])
                    elif electricity_bill:
                        sync_payment_bills(electricity_bill_ids=[electricity_bill.pk])
                messages.success(request, f"Payment of ₹{amount} recorded successfully!")
            except Exception as e:
                messages.error(request, f"Payment recording failed: {e}")
        else:
            messages.error(request, "Invalid payment details or agreement not found.")

    next_url = request.META.get("HTTP_REFERER") or reverse("rent_management")
    return HttpResponseRedirect(next_url)


# ==============================================================================
# ELECTRICITY VIEWS
# ==============================================================================

@login_required
def electricity_bill_list(request):
    owner = request.user
    ctx = get_common_context(request)

    bills = ElectricityBill.objects.filter(
        meter__room__property__owner=owner
    ).select_related("meter__room__property", "reading").order_by("-billing_month")

    total_consumption = bills.aggregate(total=Sum("units_consumed"))["total"] or Decimal("0.00")
    total_billed = bills.aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00")
    total_collected = bills.aggregate(total=Sum("amount_paid"))["total"] or Decimal("0.00")
    pending = max(Decimal("0.00"), total_billed - total_collected)

    bill_items = []
    for b in bills:
        active_ag = RentalAgreement.objects.filter(room=b.meter.room, status="ACTIVE").select_related("tenant").first()
        bill_items.append({
            "bill": b,
            "tenant": active_ag.tenant if active_ag else None,
        })

    ctx.update({
        "bills": bill_items,
        "total_consumption": total_consumption,
        "total_billed": total_billed,
        "total_collected": total_collected,
        "pending_amount": pending,
    })
    return render(request, "electricity/electricity_bill_list.html", ctx)


@login_required
def electricity_bill_form(request):
    owner = request.user
    ctx = get_common_context(request)

    if request.method == "POST":
        meter_id = request.POST.get("meter_id")
        meter = get_object_or_404(ElectricityMeter, pk=meter_id, room__property__owner=owner)
        reading_date = request.POST.get("reading_date") or timezone.localdate().isoformat()
        prev_reading = Decimal(request.POST.get("previous_reading", "0"))
        curr_reading = Decimal(request.POST.get("current_reading", "0"))
        rate = Decimal(request.POST.get("rate_per_unit") or meter.room.property.electricity_rate or "8.00")

        if curr_reading < prev_reading:
            messages.error(request, "Current reading cannot be lower than previous reading.")
        else:
            with transaction.atomic():
                reading, _ = MeterReading.objects.get_or_create(
                    meter=meter,
                    reading_date=reading_date,
                    defaults={
                        "previous_reading": prev_reading,
                        "current_reading": curr_reading,
                    }
                )
                units = curr_reading - prev_reading
                total = units * rate
                today = timezone.localdate()
                due_date = today.replace(day=min(20, 28))
                bill, created = ElectricityBill.objects.get_or_create(
                    meter=meter,
                    reading=reading,
                    defaults={
                        "billing_month": today.replace(day=1),
                        "units_consumed": units,
                        "rate_per_unit": rate,
                        "total_amount": total,
                        "due_date": due_date,
                        "status": "PENDING",
                    }
                )
                messages.success(request, f"Recorded reading and generated bill for ₹{total} (Meter: {meter.meter_number})!")
                return redirect("electricity_bill_list")

    meters = ElectricityMeter.objects.filter(room__property__owner=owner, is_active=True).select_related("room__property")
    meter_data = []
    for m in meters:
        latest_reading = MeterReading.objects.filter(meter=m).order_by("-reading_date").first()
        prev_val = latest_reading.current_reading if latest_reading else Decimal("0.00")
        meter_data.append({
            "meter": m,
            "latest_reading": prev_val,
        })
    ctx["meters"] = meter_data
    return render(request, "electricity/electricity_bill_form.html", ctx)


# ==============================================================================
# INVOICES, REPORTS & NOTIFICATIONS VIEWS
# ==============================================================================

@login_required
def invoice_list(request):
    owner = request.user
    ctx = get_common_context(request)

    rent_records = RentRecord.objects.filter(
        agreement__room__property__owner=owner
    ).select_related("agreement__tenant", "agreement__room__property").order_by("-billing_month")[:20]

    electricity_bills = ElectricityBill.objects.filter(
        meter__room__property__owner=owner
    ).select_related("meter__room__property", "reading").order_by("-billing_month")[:20]

    invoices = []
    for r in rent_records:
        invoices.append({
            "id": f"INV-RNT-{r.pk:04d}",
            "type": "RENT",
            "tenant_name": r.agreement.tenant.full_name,
            "property_name": r.agreement.room.property.name,
            "room_number": r.agreement.room.room_number,
            "amount": r.rent_amount,
            "amount_paid": r.amount_paid,
            "date": r.billing_month,
            "due_date": r.due_date,
            "status": r.status,
            "raw_obj": r,
        })
    for b in electricity_bills:
        ag = RentalAgreement.objects.filter(room=b.meter.room, status="ACTIVE").select_related("tenant").first()
        invoices.append({
            "id": f"INV-ELC-{b.pk:04d}",
            "type": "ELECTRICITY",
            "tenant_name": ag.tenant.full_name if ag else "Vacant Meter",
            "property_name": b.meter.room.property.name,
            "room_number": b.meter.room.room_number,
            "amount": b.total_amount,
            "amount_paid": b.amount_paid,
            "date": b.billing_month,
            "due_date": b.due_date,
            "status": b.status,
            "raw_obj": b,
        })

    invoices.sort(key=lambda x: str(x["date"]), reverse=True)
    ctx["invoices"] = invoices
    return render(request, "invoices/invoice_list.html", ctx)


@login_required
def reports(request):
    owner = request.user
    ctx = get_common_context(request)

    properties = Property.objects.filter(owner=owner)
    rooms = Room.objects.filter(property__owner=owner)
    total_properties = properties.count()
    total_rooms = rooms.count()
    occupied_rooms = rooms.filter(status="OCCUPIED").count()
    vacant_rooms = max(0, total_rooms - occupied_rooms)
    occupancy_rate = round(occupied_rooms / total_rooms * 100, 1) if total_rooms > 0 else 0

    payments = Payment.objects.filter(agreement__room__property__owner=owner, status="COMPLETED")
    total_revenue = payments.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

    rent_records = RentRecord.objects.filter(agreement__room__property__owner=owner)
    total_rent_expected = rent_records.aggregate(total=Sum("rent_amount"))["total"] or Decimal("0.00")
    total_rent_collected = rent_records.aggregate(total=Sum("amount_paid"))["total"] or Decimal("0.00")
    total_rent_outstanding = max(Decimal("0.00"), total_rent_expected - total_rent_collected)
    collection_rate = round(total_rent_collected / total_rent_expected * 100, 1) if total_rent_expected > 0 else 0

    electricity_bills = ElectricityBill.objects.filter(meter__room__property__owner=owner)
    total_electricity_billed = electricity_bills.aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00")

    # Property-level breakdown
    prop_stats = []
    for p in properties:
        p_rooms = rooms.filter(property=p)
        p_total = p_rooms.count()
        p_occ = p_rooms.filter(status="OCCUPIED").count()
        p_rent_recs = rent_records.filter(agreement__room__property=p)
        p_exp = p_rent_recs.aggregate(total=Sum("rent_amount"))["total"] or Decimal("0.00")
        p_col = p_rent_recs.aggregate(total=Sum("amount_paid"))["total"] or Decimal("0.00")
        p_pend = max(Decimal("0.00"), p_exp - p_col)
        p_rate = round(p_col / p_exp * 100, 1) if p_exp > 0 else (100.0 if p_exp == 0 and p_occ > 0 else 0.0)

        prop_stats.append({
            "property": p,
            "total_rooms": p_total,
            "occupied_rooms": p_occ,
            "occupancy_rate": round(p_occ / p_total * 100, 1) if p_total > 0 else 0,
            "expected_rent": p_exp,
            "collected_rent": p_col,
            "pending_rent": p_pend,
            "collection_rate": p_rate,
        })

    ctx.update({
        "total_properties": total_properties,
        "total_rooms": total_rooms,
        "occupied_rooms": occupied_rooms,
        "vacant_rooms": vacant_rooms,
        "occupancy_rate": occupancy_rate,
        "total_revenue": total_revenue,
        "total_rent_expected": total_rent_expected,
        "total_rent_collected": total_rent_collected,
        "total_rent_outstanding": total_rent_outstanding,
        "collection_rate": collection_rate,
        "total_electricity_billed": total_electricity_billed,
        "property_stats": prop_stats,
    })
    return render(request, "reports/reports.html", ctx)


@login_required
def notifications(request):
    owner = request.user
    ctx = get_common_context(request)

    notifications_list = Notification.objects.filter(tenant__owner=owner).order_by("-created_at")
    ctx["notifications"] = notifications_list
    return render(request, "notifications.html", ctx)


@login_required
def mark_notification_read(request, pk):
    notif = get_object_or_404(Notification, pk=pk, tenant__owner=request.user)
    notif.is_read = True
    notif.read_at = timezone.now()
    notif.save(update_fields=["is_read", "read_at"])
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"status": "ok"})
    return redirect("notifications")


@login_required
def generate_notifications_view(request):
    if request.method == "POST":
        result = generate_notifications(days_ahead=3, owner=request.user)
        created = result.get("created_count", 0)
        messages.success(request, f"Generated {created} payment reminder notifications.")
    return redirect("notifications")


@login_required
def settings_view(request):
    ctx = get_common_context(request)
    return render(request, "settings.html", ctx)


@login_required
def global_search(request):
    owner = request.user
    q = request.GET.get("q", "").strip()
    if not q:
        return JsonResponse({"results": []})

    properties = Property.objects.filter(owner=owner).filter(
        Q(name__icontains=q) | Q(address__icontains=q) | Q(city__icontains=q)
    )[:5]

    rooms = Room.objects.filter(property__owner=owner).filter(
        Q(room_number__icontains=q) | Q(property__name__icontains=q)
    ).select_related("property")[:5]

    tenants = Tenant.objects.filter(owner=owner).filter(
        Q(full_name__icontains=q) | Q(email__icontains=q) | Q(phone__icontains=q)
    )[:5]

    results = []
    for p in properties:
        results.append({
            "type": "Property",
            "title": p.name,
            "subtitle": f"{p.city}, {p.state}",
            "url": reverse("property_detail", kwargs={"pk": p.pk}),
        })
    for r in rooms:
        results.append({
            "type": "Room",
            "title": f"Room {r.room_number}",
            "subtitle": f"{r.property.name} ({r.status})",
            "url": reverse("rooms"),
        })
    for t in tenants:
        results.append({
            "type": "Tenant",
            "title": t.full_name,
            "subtitle": t.phone,
            "url": reverse("tenant_profile_id", kwargs={"pk": t.pk}),
        })

    return JsonResponse({"results": results})
