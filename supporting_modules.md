# Supporting Modules (Notifications, Support, Settings)

This document covers the “supporting” in-app modules that make RAAMP feel complete and safe in production:

- **Notifications** (inbox + realtime)
- **Support / Complaints** (tickets, attachments, comments, admin actions)
- **Settings** (preferences + security entry points + integrations navigation)

It documents current features, key routes/files, expected UX behavior, and remaining gaps / good-to-haves.

---

## 1) Notifications module

### Purpose
- Provide an in-app **notifications inbox** (read/unread, delete, clear-all).
- Provide **realtime delivery** via WebSocket for “new notification” events.
- Keep user messaging **safe** (no developer/internal errors exposed).

### Frontend
- **Context / state**: `raamp-frontend/src/contexts/NotificationContext.tsx`
  - Holds `notifications`, `unreadCount`, `loading`, pagination state (`hasMore`, `loadingMore`)
  - Implements optimistic actions:
    - `markAsRead(id)`
    - `markAllAsRead()`
    - `deleteNotification(id)`
    - `clearAllNotifications()`
  - Implements list pagination:
    - `fetchNotifications({ limit, offset, append })`
    - `loadMore()` (appends next page)
  - **WS behavior**:
    - Connects to `/api/notifications/ws`
    - Sends periodic `"ping"` to keep the socket alive
    - Rate-limited user toast when realtime disconnects

- **Inbox page**: `raamp-frontend/src/pages/Notifications.tsx`
  - Search filter by title/message/type
  - “Mark All Read”
  - “Clear All” confirmation dialog
  - Per-notification actions: mark read + delete
  - **Load more** button when not searching and `hasMore === true`

### Backend
- **Router**: `raamp-backend/presentation/routers/notification_router.py`
  - `GET /api/notifications?limit=&offset=&unread_only=` → list + unread count
  - `GET /api/notifications/unread/count`
  - `PATCH /api/notifications/{id}/read`
  - `POST /api/notifications/read-all`
  - `DELETE /api/notifications/{id}`
  - `DELETE /api/notifications/all`
  - `WS /api/notifications/ws` (realtime push channel)

- **Service**: `raamp-backend/application/services/notification_service.py`
  - `create_and_send(...)`:
    - checks **notification settings preferences**
    - persists notification (if allowed)
    - pushes websocket message `{ event: "new_notification", data: {...} }` (if push allowed)

- **Repository**: `raamp-backend/infrastructure/repositories/notification_repository.py`
  - `get_by_user_id(user_id, limit, offset, unread_only)` supports pagination
  - sorting: **priority desc**, then **created_at desc**

### Notification types and triggers (what creates notifications)
Notification types are defined in `raamp-backend/infrastructure/database/models/notification_model.py` as `NotificationType`:

- **`social_post`**: scheduled post lifecycle events
  - created by `NotificationService` helpers:
    - `create_scheduled_post_success(...)`
    - `create_scheduled_post_failure(...)`
    - `create_retry_started(...)`
    - `create_retry_success(...)`
    - `create_retry_failed_permanently(...)`
    - `create_reminder_10min_before(...)`
- **`alert`**: warnings that typically require user action
  - example: `create_token_expiry_warning(...)` for expiring Meta tokens
- **`system`**: internal system health alerts
  - example: `create_job_health_alert(...)` for scheduler/job issues
- **`trend_spike` / `trend_discovered`**: trend/arbitrage-related events (high-signal opportunities)
  - typically sent with metadata (e.g. `sub_type: "trend"`) so UI can drive actions like “Launch Campaign”
- **`billing`**: billing/subscription/wallet related notifications (depends on billing flow integration)
- **`campaign`**: campaign-related updates (creation, deployment, performance)
- **`ai_creative`**: Creative Studio / generation-related events (generation complete, warnings, etc.)
- **`message` / `reminder`**: user-facing informational or reminder events (generic bucket)

Important note:
- The list above documents **what the system is designed to support** and where triggers exist in code today (notably `social_post`, `alert`, `system`). For other types (`billing`, `campaign`, `ai_creative`, `trend_*`, etc.), the type exists and can be emitted, but the exact trigger locations depend on which flows call `NotificationService.create_and_send(...)`.

### Auth strategy (important)
Realtime auth currently supports multiple methods to match the main app auth strategy:
- **Query token**: `wss://.../api/notifications/ws?token=...`
- **Authorization header**: `Authorization: Bearer <token>` (supported server-side)
- **Cookie**: `access_token` cookie (supported server-side)

Note: browser WebSocket API cannot set custom headers easily; query token and/or cookies are the practical client-side options.

### UX rules (current behavior)
- If fetching notifications fails: user sees a **safe toast** (“Notifications unavailable…”).
- If mark-read/delete actions fail: user sees **safe error toasts** and the list is re-fetched to recover.

### Retention / cleanup policy
Current state:
- A TTL index exists on `notifications.created_at` (default **180 days**), so old notifications are **cleaned up automatically**.

Recommended production policy:
- Keep TTL retention in the **90–180 day** range (current: **180 days**) OR run a scheduled cleanup job per user.
- Optionally enforce a “cap” per user (see below) by periodically deleting older notifications beyond a threshold.

### Max notifications per user (limits)
Current state:
- There is **no hard max** enforced per user in code.
- The API supports pagination via `limit`/`offset`; the UI defaults to loading **20 at a time** and allows “Load more”.

Recommended production limit:
- Decide a cap (example: **2,000 notifications per user**) and prune oldest beyond the cap, or rely on TTL retention.

### Known gaps / good-to-haves
- **Load more UX**: implemented (infinite scroll with a “Load more” fallback).
- **Unread-only UI toggle**: implemented.
- **Notification grouping**: implemented (“Today”, “Earlier”).
- **Admin/system notification creation**: `POST /api/notifications` exists (primarily internal/dev). In production it should be restricted to internal service calls or admin-only.

---

## 2) Support / Complaints module

### Purpose
- Provide an in-app support “tickets” experience:
  - users submit complaints
  - upload attachments
  - follow status updates and comments
  - optionally delete/cancel **pending** complaints
- Ensure user messaging is clear and never exposes backend internals.

### Complaint status change notifications (in-app + email)
When support/admin updates a complaint status (via admin endpoints), the system now:
- Sends an **in-app notification** (`NotificationType.MESSAGE`) to the user’s notifications inbox.
- Sends a best-effort **email** (“RAAMP Support — Ticket Updated”) including:
  - complaint id + subject
  - previous status → new status
  - optional `adminResponse` snippet (if present)

### Frontend
- **Main page**: `raamp-frontend/src/pages/Complaints.tsx`
  - Uses standard in-app header via `Layout breadcrumbItems=[...]`
  - Tabs:
    - **Recent Issues / Open**: derived from statuses (`pending`, `in_progress`, `in progress`)
    - **Resolved**: `resolved` and `rejected`
  - Pagination:
    - `pageSize = 20`
    - “Load more” behavior via `getUserComplaintsPaginated(limit, offset)`
  - Detail modal (`Dialog`):
    - view subject/description/priority/status
    - view attachments (open links)
    - view comment history + add a comment
    - edit complaint fields **only when status is `pending`**
  - Phone UX:
    - “Copy/Call” actions are hidden until user clicks the phone number
  - Delete UX:
    - Delete button for **pending** complaints
    - shows safe, user-friendly failure messages if delete is not allowed
  - Filtering/search:
    - search by id/subject/description/status/priority
    - date filter: all time / last 7 days / last 30 days

- **Client service**: `raamp-frontend/src/services/complaintService.ts`
  - Implements submit, list (paginated), update, delete, add comment, upload attachment, etc.

### Backend
- **Router**: `raamp-backend/presentation/routers/complaints_router.py`
  - `POST /api/complaints/submit`
  - `GET /api/complaints/user?limit=&offset=`
  - `PUT /api/complaints/{complaint_id}` (edit pending only)
  - `DELETE /api/complaints/{complaint_id}` (delete pending only)
  - `POST /api/complaints/{complaint_id}/comments`
  - `POST /api/complaints/{complaint_id}/attachments` (10MB limit)
  - `POST /api/complaints/{complaint_id}/rating` (resolved only)
  - Admin endpoints (require `is_admin`):
    - `POST /api/complaints/admin/{complaint_id}/resolve`
    - `POST /api/complaints/admin/{complaint_id}/status`

- **Service**: `raamp-backend/application/services/complaint_service.py`
  - `submit_complaint(...)` creates complaint and triggers a fire-and-forget acknowledgement email:
    - apology + included description + “2–3 business days” SLA
  - `get_complaints_for_user(user_id, limit, offset)` returns normalized dicts for frontend
  - `admin_update_status(...)` appends status updates + can set `adminResponse`
    - also triggers **in-app notification + email** to the complaint owner
  - `upload_attachment(...)` uploads to **Cloudinary authenticated delivery**, stores a reference in DB, and returns a **signed URL**

### Status logic (current)
- **Editable/Deletable**: only `status == "pending"`
- **“Open” tab** (frontend): `pending`, `in_progress`, `in progress`
- **“Resolved” tab** (frontend): `resolved`, `rejected`

### UX rules (current)
- Complaint submission shows a user-facing success message (apology + SLA) and sends acknowledgement email.
- Backend 5xx errors are sanitized to user-safe messages (no stack traces/details).

### Known gaps / good-to-haves
- **Admin UI**: admin endpoints exist but there is no in-app admin/support panel to use them.
- **Attachment storage security (must-fix for production)**:
  - Local disk storage is not production-safe (backup/retention, access control, and scaling risks).
  - Complaint attachments are stored in **Cloudinary authenticated delivery** and exposed via **signed URLs** generated server-side.
  - The DB stores attachment **references** (not public URLs); the API returns signed URLs to the owner.
  - If you need true time-limited access, use Cloudinary **auth tokens** or an **authenticated proxy** endpoint.
- **Rate limiting / spam protection**: basic in-memory cooldown exists; production should use Redis/gateway rate limiting.
- **Filtering/search**: implemented in UI.

---

## 3) Settings module

### Purpose
- Provide a home for user preferences and account-related tools:
  - notification preferences
  - security entry points
  - integrations management entry points
  - business specialties settings

### Frontend
- **Settings landing**: `raamp-frontend/src/pages/Settings.tsx`
  - cards link to:
    - `/profile/user` (Edit user profile)
    - `/profile/business-setup`
    - `/settings/business-specialties`
    - `/profile/brand-settings`
    - `/settings/notifications` (Notification Preferences)
    - `/settings/integrations` (Integrations)
    - (Security settings are intentionally hidden; see below)

- **Notification Preferences**: `raamp-frontend/src/pages/NotificationPreferences.tsx`
  - Fetches via `authService.getNotificationSettings()`
  - Shows explicit **error state + Retry** if load fails (no silent failures)
  - Save uses safe toast messages (no raw backend details)
  - Edit is gated by `PasswordVerificationDialog` (“Unlock to Edit”)

- **Integrations**: `raamp-frontend/src/pages/SettingsIntegrations.tsx` → reuses `Onboarding` UI under a settings route.

- **Account & Security**: `raamp-frontend/src/pages/AccountSecurity.tsx`
  - Uses safe, sanitized toasts (no raw `error.message` / backend detail leakage)
  - Includes account deletion OTP flow (email OTP)
  - Password change flow now lives directly inside **Account & Security** (OTP + current password + new password)
  - Security settings preferences UI is **intentionally hidden** post-FYP (see below)
  - **Gap**: does not provide “Active Sessions” view/revoke UI (see Session management)

### Password change flow (OTP) — current behavior + explicit security/UX gaps
Current implementation:
- UI lives in `raamp-frontend/src/pages/AccountSecurity.tsx`
- Backend endpoints in `raamp-backend/presentation/routers/auth_router.py`:
  - `POST /api/auth/change-password/send-otp`
  - `POST /api/auth/change-password` (verifies OTP then updates password hash)

Explicit gaps to be aware of:
- **Security gap (OTP-only, no current password)**: **fixed**
  - Password change now requires **current password + OTP** (backend enforces it).
- **Dead frontend field**: **fixed**
  - `currentPassword` is now shown in the UI and sent to the backend for verification.
- **UX fragmentation**: fixed
  - Password change no longer redirects to Edit Profile; it’s handled in Account & Security.
- **Error message leakage risk (now fixed)**:
  - Previously, the catch block would stringify backend `err.errors` and show it in a toast.
  - This is now sanitized to a generic user-safe error message.

### Backend
- **Settings router**: `raamp-backend/presentation/routers/settings_router.py` (prefix `/api/settings`)
  - Notification settings:
    - `GET /api/settings/notifications`
    - `POST /api/settings/notifications`
  - Security settings (deferred; intentionally not exposed in UI post-FYP):
    - `GET /api/settings/security`
    - `POST /api/settings/security`
  - Business specialties:
    - `PATCH /api/settings/business/specialties`
    - `GET /api/settings/business/specialties`

### Routing / deep linking
- Settings routes are registered in the SPA router:
  - `raamp-frontend/src/App.tsx` contains `/settings/*` routes, so deep linking works.

### Known gaps / good-to-haves
- **Consistency in backend logging**: fixed (replaced `print(...)` with structured logging).
- **First-run settings 404 behavior**: fixed
  - Backend auto-creates defaults for `GET /api/settings/notifications` and `GET /api/settings/security` when missing.
- **Security settings (intentionally hidden — backend exists but not exposed; deferred post-FYP)**:
  - Backend supports storing/fetching security preferences, but they are **not enforced** in auth flows yet.
  - To avoid misleading “security controls” that do nothing, the UI **does not surface** these toggles for now.
  - Stored (but currently unenforced) fields include:
    - `two_factor_enabled`
    - `login_alerts`
    - `session_timeout_minutes`
    - `trusted_devices_only`
    - `password_change_required`
- **Session management (Active Sessions) is not implemented**:
  - There is no backend session registry and no endpoint to list/revoke sessions.
  - With current stateless JWT-based auth, “revoke a single device/session” requires adding a server-side session store (or token versioning/denylist).
- **Integrations error UX**:
  - **Status**: improved for demo-safety.
  - Integrations UI (reused `Onboarding` under `SettingsIntegrations`) now shows **safe toasts** for key failure points (status fetch, disconnect failures, Google Maps location failures) instead of failing silently.
  - Google Maps connect modal uses toasts instead of blocking `alert(...)`.

---

## Cross-module production checklist (quick)

### Error safety
- Backend routers have been updated to avoid returning raw exception strings in HTTP `detail` fields.
- Frontend toasts are expected to display **generic** user messages and avoid raw backend details.

### Scalability
- Notifications: pagination via `limit/offset` + “Load more”
- Complaints: pagination via `limit/offset` + “Load more”
- Settings: mostly small data; no special scaling issues

### Missing UI for existing backend features
- Complaints admin endpoints exist but have no admin UI.

---

## High priority gaps (tracking)

### Admin UI for Support/Complaints
- **Backend exists**: `/api/complaints/admin/{complaint_id}/status` and `/api/complaints/admin/{complaint_id}/resolve`
- **Backend list exists**: `GET /api/complaints/admin?limit=&offset=&status_filter=&q=` (admin-only) for queue view
- **Why it matters**: support team cannot manage tickets without calling APIs directly.
- **Status**: admin UI at `/admin/complaints` can now render a basic ticket queue (paginated list endpoint added).

### Active Sessions management
- **Status**: not implemented (no session registry, no revoke mechanism).
- **Why it matters**: cannot “log out other devices” with stateless JWT.
- **Fix options**:
  - server-side session store (recommended) + per-session revoke
  - token denylist/token version strategy + short-lived access tokens

### Rate limiting on Support submissions
- **Status**: basic in-memory cooldown added to `POST /api/complaints/submit` (per-process; production should use Redis or gateway rate limiting).

### Notification retention/cleanup
- **Status**: TTL index added on `notifications.created_at` (default 180 days).
- **Why it matters**: prevents unbounded growth of notifications collection.

