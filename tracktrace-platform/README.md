# Track & Trace — logistics shipment platform

A shipment tracking and logistics operations platform: public tracking, a customer portal, and a staff
console for managing shipments, quotes, contact messages, and users. Built from an original specification
inspired by the general functionality of nationswaytransport.com/track-and-trace (no copied code, text,
or branding). **This platform has no payment functionality anywhere, by design.**

## 1. Project overview
- Customers track shipments publicly with no login, or create an account to see their own shipment
  history, documents, and notifications.
- Staff (STAFF / OPERATIONS / ADMIN / SUPER_ADMIN) create and update shipments, add tracking events,
  manage customers, quotes, contact messages, and (for ADMIN+) users and site settings.
- Every shipment status/location change is a new, permanent tracking event - history is never overwritten.
- English and French throughout, switchable at runtime.

## 2. Architecture
```
/backend    FastAPI + SQLAlchemy + Alembic + PostgreSQL, JWT-in-cookie auth with CSRF double-submit
/frontend   React + TypeScript + Vite, react-router, i18next (en/fr)
/tests      (backend tests live in backend/tests; this folder is reserved for cross-stack/e2e notes)
/docs       Deployment, backup/recovery, design plan
/scripts    top-level helper scripts (currently unused; per-package scripts live in backend/scripts)
```
Backend and frontend deploy independently (Render native Python + Cloudflare Pages + Neon; see `docs/DEPLOYMENT.md`). Docker is not required.

## 3. Requirements
- Python 3.12+
- Node.js 20+
- PostgreSQL 14+ (no SQLite fallback, anywhere)

## 4. Installation
```
git clone <this repo>
cd tracktrace-platform

# Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env   # edit as needed

# Frontend
cd ../frontend
npm install
cp .env.example .env
```

## 5. Environment variables
See `backend/.env.example` and `frontend/.env.example`. Nothing sensitive is committed; `.env` is
git-ignored. In production, `SECRET_KEY`/`JWT_SECRET` must be random 32+ character values, and
`COOKIE_SECURE=true` is enforced by the app's config validator.

## 6. Database setup
```
createdb tnt_dev   # see docs/DEPLOYMENT.md section 9 for the exact role/database commands
```

## 7. Migrations
```
cd backend
export DATABASE_URL=postgresql+psycopg://tnt:tnt_dev_pw@localhost:5432/tnt_dev
alembic upgrade head
```
This applies the schema (18 tables — see `backend/app/models/`) plus reference data (17 shipment
statuses in 16 languages, service types, FAQ — not demo data). There are 5 migrations; they build the
whole database from an empty PostgreSQL database.

Development-only demo data (three sample shipments `DEMO-001`..`DEMO-003`, four sample accounts):
```
ENVIRONMENT=development python scripts/seed_dev.py
```
The script prints a random password for each demo account **once** (they are not stored anywhere else):
`admin@example.com` (super admin), `staff@example.com`, `customer1@example.com`, `customer2@example.com`.
Staff sign in at `/login`. It refuses to run when `ENVIRONMENT=production`; never use it on a real deployment
- create the first real admin with `python scripts/create_admin.py` instead.

## 8. Running locally
**Run natively:**
```
# terminal 1
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload

# terminal 2
cd frontend && npm run dev
```
Frontend: http://localhost:5173 · Backend: http://localhost:8000 · API docs: http://localhost:8000/docs

Quick check once both are running (after seeding): open http://localhost:5173/track/DEMO-001 - no account
needed. Nothing in this project requires Docker.


## 9. Running tests
```
cd backend
export TEST_DATABASE_URL=postgresql+psycopg://tnt:tnt_dev_pw@localhost:5432/tnt_test
python -m pytest tests/ -v
ruff check app
```
Backend tests run against a **real PostgreSQL database** (created/migrated fresh each session), not
SQLite or mocks. 71 tests cover auth, RBAC, cross-customer data isolation, tracking-number uniqueness,
status-history preservation, the Failed-Delivery-Attempt and Returned-to-Sender milestones, public-tracking
privacy, shipment notification dispatch (skipped / sent / failed), rate limiting, document upload security,
and audit logging. The frontend has 72 Vitest tests.

```
cd frontend
npx tsc -b --noEmit   # typecheck
npm run build         # production build
npx vitest run        # frontend tests
npm run lint          # oxlint
```

## 10. Production deployment
See `docs/DEPLOYMENT.md` (Neon + native-Python Render + Cloudflare Pages, custom-domain and cookie notes) and `docs/BACKUP_AND_RECOVERY.md`.

## 11. Admin account creation
```
cd backend
python scripts/create_admin.py --email admin@yourcompany.com --name "Jane Doe"
```
Prompts for a password interactively. Creates exactly one SUPER_ADMIN and nothing else - safe to run
against production. (`scripts/seed_dev.py` is for development only and refuses to run in production.)

## 12. API documentation
Interactive OpenAPI docs at `/docs` (Swagger UI) and `/redoc` while the backend is running. Full schema
at `/openapi.json`.

## 13. Security considerations
- Argon2 password hashing; JWT access token in an httpOnly cookie + CSRF double-submit token for
  cookie-based requests (bearer tokens, used by non-browser clients, are exempt from CSRF checks).
- Backend-enforced RBAC (5 roles) and per-resource ownership checks — a customer can never reach another
  customer's shipments or documents (covered by automated tests).
- Account lockout after repeated failed logins; generic responses on login/forgot-password so accounts
  can't be enumerated.
- Uploaded files are content-sniffed (magic bytes), not trusted by extension/MIME alone; path-traversal
  guarded local storage; S3-compatible storage option for production.
- Rate limiting on tracking lookups, login, registration, forgot-password, and public forms.
- Uniform error envelope; stack traces are logged, never returned to clients.
- See `docs/DEPLOYMENT.md` for the production checklist (cookie/CORS/secret validation is enforced by the
  app itself — it refuses to start in an unsafe production configuration).

## 14. Backup strategy
See `docs/BACKUP_AND_RECOVERY.md`.

## Tracking behaviour (what customers see)
- **No account is needed to track.** `/track` accepts a tracking number; `/track/<NUMBER>` is a direct,
  shareable link (a Share button uses the device share sheet or copies the link). Only the tracking number
  identifies the shipment, and the public response contains no contact details, internal notes, documents
  or staff data (enforced by a test that checks the exact list of returned fields).
- **Real events only.** Every status/location change is an append-only tracking event recorded by staff.
  The page shows a concise *Latest update* by default and a *View Full Tracking History* button that expands
  the complete timeline (oldest to newest) and collapses again; it works with mouse, touch and keyboard.
- **Milestones**: Shipment Created, Pickup Scheduled, Picked Up, Origin Facility, Processing, Departed
  Origin, In Transit, Arrived at Facility, Customs/Clearance, Destination Facility, Out for Delivery,
  Delivered, Delayed, Exception, **Failed Delivery Attempt**, **Returned to Sender**, Cancelled. Staff can
  add more under Staff -> Statuses. *Returned to Sender* and *Delivered* are final: only an administrator
  can reopen a finished shipment. A returned parcel never shows a delivery date.
- **Honest estimates.** An ETA appears only if staff recorded one; otherwise the page says "Estimated
  delivery date unavailable". "On track / past the estimated date / delivered on time" are computed from
  real recorded dates only.
- **No GPS and no maps.** Progress is milestone-based. Nothing simulates vehicle movement.
- Notifications (email/SMS/WhatsApp) are only sent when provider credentials are configured; otherwise they
  are recorded as `SKIPPED_NOT_CONFIGURED`, never as sent.

## No payment functionality
Verified two ways: (1) no payment-related models, routes, dependencies, or frontend pages exist anywhere
in this repository; (2) an automated test (`test_no_payment_routes_exist`) fails the build if any endpoint
path ever contains a payment/checkout/billing-related keyword.
