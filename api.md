# KirayaSetu Backend — React Integration API Contract

**API version:** v1 (current Django URL layout; no `/v1/` prefix)  
**Backend:** Django + Django REST Framework + MySQL  
**Authentication:** Django session cookie + CSRF protection  
**Content type:** `application/json` unless an endpoint says otherwise

This file describes the routes and request/response contract in this repository. All business-data APIs require an authenticated owner session. The API filters data by the logged-in owner; clients must not send an `owner` ID to choose whose data to read or write.

## 1. Local environment

Use one hostname consistently for frontend and backend during local development. The examples use:

- React/Vite: `http://localhost:5173`
- Django API: `http://localhost:8000`

Do not mix `localhost` and `127.0.0.1` for the browser app and API: the session/CSRF cookies may not be shared as expected. The configured CORS and CSRF trusted origins must exactly match the React origin.

Base URL:

```text
http://localhost:8000
```

Trailing slashes are part of the routes.

## 2. Session and CSRF authentication

The backend uses session authentication, not bearer/JWT tokens. Browser calls must use `credentials: "include"`. A CSRF token is required for unsafe methods such as `POST`, `PUT`, `PATCH`, and `DELETE`.

### 2.1 Obtain the CSRF cookie

```http
GET /api/auth/csrf/
```

Example response:

```json
{"detail":"CSRF cookie set."}
```

The response sets a `csrftoken` cookie.

### 2.2 React fetch helper

```javascript
const API_BASE = "http://localhost:8000";

function readCookie(name) {
  const prefix = `${name}=`;
  const value = document.cookie
    .split(";")
    .map((part) => part.trim())
    .find((part) => part.startsWith(prefix));
  return value ? decodeURIComponent(value.slice(prefix.length)) : null;
}

export async function apiFetch(path, options = {}) {
  const method = (options.method || "GET").toUpperCase();
  const headers = new Headers(options.headers || {});
  const unsafe = !["GET", "HEAD", "OPTIONS", "TRACE"].includes(method);

  if (options.body && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  if (unsafe) {
    const token = readCookie("csrftoken");
    if (token) headers.set("X-CSRFToken", token);
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    method,
    headers,
    credentials: "include",
  });

  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const error = new Error(`API request failed (${response.status})`);
    error.status = response.status;
    error.data = data;
    throw error;
  }
  return data;
}

export async function getCsrfCookie() {
  return apiFetch("/api/auth/csrf/");
}
```

Call `getCsrfCookie()` before registration and login. Call it again if the CSRF cookie/token is missing or expired. Once logged in, the browser sends the `sessionid` cookie automatically with `credentials: "include"`.

### 2.3 Authentication endpoints

| Method | Endpoint | Auth | Purpose |
|---|---|---|---|
| `GET` | `/api/auth/csrf/` | Public | Set CSRF cookie |
| `POST` | `/api/auth/register/` | Public + CSRF required | Create owner account |
| `POST` | `/api/auth/login/` | Public + CSRF required | Start owner session |
| `POST` | `/api/auth/logout/` | Login + CSRF required | End current session |
| `GET` | `/api/auth/me/` | Login required | Current owner profile |

Register request:

```json
{
  "username": "owner_demo",
  "email": "owner@example.com",
  "password": "Use-A-Strong-Unique-Password!"
}
```

Successful register response (`201`):

```json
{
  "id": 12,
  "username": "owner_demo",
  "email": "owner@example.com"
}
```

Passwords are write-only and are never returned. Password strength uses Django's configured validators.

Login request (`identifier` can be username or email):

```json
{
  "identifier": "owner_demo",
  "password": "Use-A-Strong-Unique-Password!"
}
```

Successful login response (`200`):

```json
{
  "detail": "Login successful.",
  "user": {
    "id": 12,
    "username": "owner_demo",
    "email": "owner@example.com"
  }
}
```

Current user response (`GET /api/auth/me/`):

```json
{"id":12,"username":"owner_demo","email":"owner@example.com"}
```

Logout request body can be `{}`. Success response:

```json
{"detail":"Logout successful."}
```

## 3. API endpoint inventory

Every business-data route below requires login and is owner-scoped. Detail endpoints return `404 Not Found` when the record does not belong to the logged-in owner, even if the numeric ID exists for another owner.

| Resource | List / create | Detail / update / delete |
|---|---|---|
| Properties | `GET, POST /api/properties/` | `GET, PUT, PATCH, DELETE /api/properties/{id}/` |
| Rooms | `GET, POST /api/properties/rooms/` | `GET, PUT, PATCH, DELETE /api/properties/rooms/{id}/` |
| Tenants | `GET, POST /api/tenants/` | `GET, PUT, PATCH, DELETE /api/tenants/{id}/` |
| Rental agreements | `GET, POST /api/tenants/rental-agreements/` | `GET, PUT, PATCH, DELETE /api/tenants/rental-agreements/{id}/` |
| Rent records | `GET, POST /api/billing/` | `GET, PUT, PATCH, DELETE /api/billing/{id}/` |
| Electricity meters | `GET, POST /api/electricity/meters/` | `GET, PUT, PATCH, DELETE /api/electricity/meters/{id}/` |
| Meter readings | `GET, POST /api/electricity/readings/` | `GET, PUT, PATCH, DELETE /api/electricity/readings/{id}/` |
| Electricity bills | `GET, POST /api/electricity/bills/` | `GET, PUT, PATCH, DELETE /api/electricity/bills/{id}/` |
| Generate electricity bill | `POST /api/electricity/bills/generate/` | — |
| Payments | `GET, POST /api/payments/` | `GET, PUT, PATCH, DELETE /api/payments/{id}/` |
| Dashboard summary | `GET /api/dashboard/` | — |
| Notifications | `GET /api/notifications/` | `GET, PATCH /api/notifications/{id}/` |
| Unread notification count | `GET /api/notifications/unread-count/` | — |
| Pending bills | `GET /api/notifications/pending-bills/` | — |
| Generate notifications | `POST /api/notifications/generate/` | — |

`GET` collection endpoints return JSON arrays, except notification pending bills (`{ "count": ..., "results": [...] }`) and summary endpoints. Pagination is not enabled in current DRF settings.

## 4. Resource fields and example payloads

Primary keys are numeric IDs. Dates use `YYYY-MM-DD`; timestamps use ISO 8601. Decimal monetary values should be sent as strings to avoid floating-point rounding in JavaScript.

### 4.1 Property

Fields: `id`, `owner`, `name`, `property_type`, `address`, `city`, `state`, `pin_code`, `monthly_rent`, `security_deposit`, `rent_due_day`, `electricity_rate`, `created_at`, `updated_at`.

`property_type`: `HOSTEL | APARTMENT | BUILDING | HOUSE | OTHER`. `owner` is read-only; the backend assigns the logged-in account automatically.

```json
{
  "name": "Sunrise Hostel",
  "property_type": "HOSTEL",
  "address": "Example Road",
  "city": "Indore",
  "state": "Madhya Pradesh",
  "pin_code": "452001",
  "monthly_rent": "8000.00",
  "security_deposit": "8000.00",
  "rent_due_day": 5,
  "electricity_rate": "8.00"
}
```

### 4.2 Room

Fields: `id`, `property`, `room_number`, `floor`, `room_type`, `monthly_rent`, `security_deposit`, `status`, `created_at`, `updated_at`.

`room_type`: `SINGLE | DOUBLE | TRIPLE | SHARED`. `status`: `VACANT | OCCUPIED | MAINTENANCE`. `property` must be owned by the signed-in owner; `room_number` is unique per property.

```json
{
  "property": 1,
  "room_number": "101",
  "floor": "1",
  "room_type": "SINGLE",
  "monthly_rent": "8000.00",
  "security_deposit": "8000.00",
  "status": "VACANT"
}
```

### 4.3 Tenant

Fields: `id`, `owner`, `full_name`, `email`, `phone`, `alternate_phone`, `date_of_birth`, `address`, `emergency_contact_name`, `emergency_contact_phone`, `created_at`, `updated_at`.

`owner` is read-only and set by the server. Example:

```json
{
  "full_name": "Rahul Sharma",
  "email": "rahul@example.com",
  "phone": "9876543210",
  "alternate_phone": "",
  "date_of_birth": "2001-04-15",
  "address": "Indore, Madhya Pradesh",
  "emergency_contact_name": "Amit Sharma",
  "emergency_contact_phone": "9876500000"
}
```

### 4.4 Rental agreement

Fields: `id`, `tenant`, `room`, `start_date`, `end_date`, `monthly_rent`, `security_deposit`, `status`, `notes`, `created_at`, `updated_at`.

`status`: `ACTIVE | COMPLETED | TERMINATED`. Tenant and room must belong to the same owner. An active agreement cannot use a maintenance room or a room that already has another active agreement.

```json
{
  "tenant": 1,
  "room": 1,
  "start_date": "2026-10-01",
  "end_date": null,
  "monthly_rent": "8000.00",
  "security_deposit": "8000.00",
  "status": "ACTIVE",
  "notes": ""
}
```

### 4.5 Rent record

Fields: `id`, `agreement`, `billing_month`, `rent_amount`, `due_date`, `amount_paid`, `status`, `notes`, `created_at`, `updated_at`.

`billing_month` should be the first day of that month. `amount_paid` and `status` are read-only through this API because they are reconciled from completed Payment records; use the Payments API to register payments.

```json
{
  "agreement": 1,
  "billing_month": "2026-10-01",
  "rent_amount": "8000.00",
  "due_date": "2026-10-05",
  "notes": "October rent"
}
```

### 4.6 Electricity meter

Fields: `id`, `room`, `meter_number`, `installation_date`, `is_active`, `notes`, `created_at`, `updated_at`.

```json
{
  "room": 1,
  "meter_number": "MTR-101",
  "installation_date": "2026-10-01",
  "is_active": true,
  "notes": "Main meter"
}
```

### 4.7 Meter reading

Fields: `id`, `meter`, `reading_date`, `previous_reading`, `current_reading`, `notes`, `created_at`.

Current and previous readings must be non-negative; current reading cannot be lower than previous reading; only one reading per meter/day is allowed.

```json
{
  "meter": 1,
  "reading_date": "2026-10-20",
  "previous_reading": "100.00",
  "current_reading": "150.00",
  "notes": "Monthly reading"
}
```

### 4.8 Electricity bill

Fields: `id`, `meter`, `reading`, `billing_month`, `units_consumed`, `rate_per_unit`, `total_amount`, `due_date`, `amount_paid`, `status`, `created_at`, `updated_at`.

A bill's meter and reading must match; readings and meters must belong to the current owner. The amount must equal units multiplied by rate; rate must match the property's configured electricity rate. `amount_paid` and `status` are read-only and reconciled from payments. Preferred create workflow:

```http
POST /api/electricity/bills/generate/
```

Request:

```json
{"reading_id": 1}
```

Success (`201` when created, `200` when a bill already exists for the reading):

```json
{
  "message": "Electricity bill generated successfully.",
  "created": true,
  "bill_id": 1,
  "meter_number": "MTR-101",
  "billing_month": "2026-10-01",
  "units_consumed": "50.00",
  "rate_per_unit": "8.00",
  "total_amount": "400.00",
  "due_date": "2026-10-05",
  "status": "PENDING"
}
```

The due day comes from the property `rent_due_day` and is clamped to the last calendar day of the month when necessary. One bill per meter reading is enforced at the database level.

### 4.9 Payment

Fields: `id`, `agreement`, `rent_record`, `electricity_bill`, `amount`, `payment_date`, `payment_method`, `status`, `transaction_reference`, `notes`, `created_at`.

Exactly one of `rent_record` or `electricity_bill` must be supplied; `agreement` is required. The chosen bill must belong to the selected agreement/room. `amount` must be greater than zero and a completed payment may not exceed the remaining balance.

```json
{
  "agreement": 1,
  "rent_record": 1,
  "electricity_bill": null,
  "amount": "2000.00",
  "payment_date": "2026-10-23T10:00:00+05:30",
  "payment_method": "UPI",
  "status": "COMPLETED",
  "transaction_reference": "UPI-REFERENCE-001",
  "notes": "Part payment"
}
```

`payment_method`: `CASH | UPI | BANK_TRANSFER | CARD | OTHER`. `status`: `PENDING | COMPLETED | FAILED | REFUNDED`. Only `COMPLETED` payments update a bill's amount paid and balance status. When a payment changes or is deleted, the linked bill balance is recalculated.

### 4.10 Dashboard response

```json
{
  "generated_at": "2026-10-23T10:00:00+05:30",
  "rooms": {"total": 10, "occupied": 6, "vacant": 3, "maintenance": 1},
  "tenants": {"active": 6, "active_agreements": 6},
  "rent": {
    "total_billed": "48000.00",
    "total_paid_towards_bills": "30000.00",
    "pending_amount": "18000.00",
    "overdue_amount": "8000.00",
    "pending_records": 4,
    "overdue_records": 2
  },
  "electricity": {
    "total_billed": "3200.00",
    "total_paid_towards_bills": "1200.00",
    "pending_amount": "2000.00",
    "overdue_amount": "400.00",
    "pending_records": 3,
    "overdue_records": 1
  },
  "payments": {
    "completed_payment_count": 8,
    "total_collected": "31200.00",
    "recent": []
  }
}
```

These numbers are illustrative only. Actual counts and totals are based solely on the signed-in owner's records. Each `payments.recent[]` item contains `id`, `tenant`, `amount`, `payment_date`, `payment_method`, `status`, `bill_type`, `bill_id`, and `transaction_reference`.

### 4.11 Notifications

List: `GET /api/notifications/`  
Optional query params: `is_read=true|false`, `notification_type=RENT_UPCOMING|RENT_OVERDUE|ELECTRICITY_UPCOMING|ELECTRICITY_OVERDUE`, `tenant_id=<id>`.

Only `is_read` is writable. Other notification fields and bill links are server-managed. Mark a notification read/unread:

```http
PATCH /api/notifications/1/
Content-Type: application/json
```

```json
{"is_read": true}
```

Unread count: `GET /api/notifications/unread-count/` → `{"unread_count": 2}`.

Pending bills: `GET /api/notifications/pending-bills/` returns:

```json
{
  "count": 1,
  "results": [
    {
      "bill_type": "RENT",
      "bill_id": 1,
      "tenant_id": 1,
      "tenant_name": "Rahul Sharma",
      "due_date": "2026-10-25",
      "total_amount": "8000.00",
      "amount_paid": "2000.00",
      "amount_due": "6000.00",
      "status": "PENDING"
    }
  ]
}
```

`POST /api/notifications/generate/` supports:

```json
{"days_ahead": 3, "as_of": "2026-10-23"}
```

Both fields are optional; `days_ahead` defaults to `3`, is constrained to `0..365`, and `as_of` defaults to the server's local date (`Asia/Kolkata`). Response includes `message`, `created_count`, `days_ahead`, and `as_of`. Generation from this API only considers the current owner's records.

## 5. Status codes and errors

| Status | Meaning |
|---|---|
| `200 OK` | Successful read, update, login, logout, or idempotent bill generation |
| `201 Created` | Resource created |
| `400 Bad Request` | Invalid fields, relationship mismatch, or validation error |
| `401 Unauthorized` or `403 Forbidden` | Not authenticated, session/permission failure, or CSRF rejection (exact status depends on authentication path) |
| `404 Not Found` | Missing record or record outside the logged-in owner's scope |
| `405 Method Not Allowed` | Method is not enabled for that endpoint |

Validation errors are generally JSON objects keyed by field; authentication/permission errors generally contain `detail`. UI code should display a generic user-friendly message for unexpected server errors and log the structured response for debugging without logging passwords or cookies.

## 6. Owner isolation and relationship rules

- `Property.owner` is set by the server to the signed-in user and cannot be selected/changed through normal API payloads.
- `Room` inherits owner scope through `Room.property.owner`.
- `Tenant.owner` is set by the server at creation. Legacy tenants with no agreement were intentionally left unassigned during migration because their owner cannot be inferred safely; they are not returned by owner-scoped APIs until an administrator assigns their owner.
- Agreements require the selected tenant and room/property to belong to the same owner.
- Rent records are scoped through agreement → room → property.
- Meters, readings, and electricity bills are scoped through meter → room → property.
- Payments are scoped through agreement → room → property and the bill must match the same agreement/room.
- Dashboard totals, notifications, unread counts, pending bills, and notification-generation operations are owner-scoped.

Never rely on hidden buttons or client-side filters for security. Do not send a chosen `owner` ID from React as an authorization mechanism. Backend querysets and validation are the source of access control.

## 7. Local checks and deployment notes

Install dependencies from `requirements.txt` and copy `.env.example` to `.env`, setting a new secret key and local MySQL credentials. Keep `.env` out of Git and never ship it to the React team.

Before applying migrations on an existing database:

1. Take a MySQL backup.
2. Verify that the `gurjar` user exists, because the confirmed migration maps the existing properties to that account.
3. Apply `python manage.py migrate`.
4. Run `python manage.py check` and the full test suite.

Ownership migration adds an owner relationship and does not remove or rename existing business fields. The migration maps existing tenants through their rental agreements. Tenants without agreements remain unassigned and are excluded from owner-scoped APIs until mapped through Django admin (Tenant list allows filtering/editing `owner`).

For production, use HTTPS, set `DJANGO_DEBUG=False`, set trusted production hosts/origins, use a strong unique `DJANGO_SECRET_KEY`, protect database credentials, and review the deployment checks. Do not run a development server as the production server.
