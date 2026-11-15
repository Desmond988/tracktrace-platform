# Deployment guide (no Docker required)

Target architecture for the first staging deployment:

```
Cloudflare Pages (React build)  ->  Render web service (FastAPI, native Python)  ->  Neon (PostgreSQL)
```

Docker is **not** needed to develop, test, or deploy this project. The `Dockerfile`s, `nginx.conf`,
`docker-compose.yml` and `render.yaml` in the repo are an optional alternative path only; nothing here
depends on them.

> Status: the software is code-complete and verified locally. It has **not** yet been validated on the
> internet. The first staging deploy is where HTTPS cookies, CORS, email delivery and file storage get
> tested for real. Items marked **[verify on first deploy]** could not be tested from the build environment.

---

## 1. Neon PostgreSQL

1. Create a Neon project and database.
2. Copy the connection string. Neon gives `postgresql://USER:PASSWORD@HOST/DB?sslmode=require`.
3. Change only the scheme so SQLAlchemy uses the psycopg 3 driver:
   `postgresql+psycopg://USER:PASSWORD@HOST/DB?sslmode=require`
4. Use Neon's **direct** (non-pooled) connection string for the first staging deploy. It avoids
   pooler-specific behaviour during migrations. **[verify on first deploy]** - not tested against Neon.
5. Neon computes suspend when idle; the first request after a pause is slower. The app uses
   `pool_pre_ping`, so dropped idle connections are replaced automatically.

No manual schema work: migrations create every table and seed reference data (see section 5).

## 2. Render backend (native Python runtime)

Create **New -> Web Service**, connect the GitHub repo, then:

| Setting | Value |
|---|---|
| Runtime / Language | **Python 3** (not Docker) |
| Root Directory | `backend` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health Check Path | `/health` |
| Instance type | Free is fine for a first look (see limitations below) |

Environment variables (all set in the Render dashboard, never committed):

| Variable | Value |
|---|---|
| `PYTHON_VERSION` | `3.12.3` (matches what the project was tested on) |
| `ENVIRONMENT` | `production` |
| `DATABASE_URL` | the Neon string from section 1 |
| `SECRET_KEY`, `JWT_SECRET` | two different random 32+ char values: `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `FRONTEND_URL` | your Cloudflare Pages URL (see section 3) |
| `CORS_ORIGINS` | the same origin, exact, no trailing slash |
| `API_URL` | this Render service's public URL |
| `COOKIE_SECURE` | `true` |
| `COOKIE_SAMESITE` | `lax` (see section 4) |
| `TRUSTED_PROXY_HEADERS` | `true` |
| `STORAGE_BACKEND` | `local` for now (see limitations) |

The app refuses to start in production if secrets are short/default, cookies aren't secure, or
CORS/frontend URLs point at localhost - a wrong config fails loudly instead of running insecurely.

### Render free-tier limitations that affect this app

- **Outbound SMTP is blocked on free web services** (ports 25/465/587, in force since 26 Sep 2025 per
  Render's changelog). This app sends email over SMTP only, so **password-reset and shipment
  emails cannot be delivered from a free Render instance even with valid SMTP credentials.** Options:
  a paid Render instance, or a different backend host. Until then the app stays honest: it logs the
  failure and records notifications as failed/skipped - it never pretends an email was sent.
  Password reset is the one place this bites, because that flow *requires* email.
- **No persistent disk on free instances.** With `STORAGE_BACKEND=local`, uploaded documents are lost
  on restart/redeploy. Fine for trying the flow; use S3-compatible storage (`STORAGE_BACKEND=s3`)
  before real documents are uploaded.
- Free instances spin down when idle, so the first request after a pause is slow.
- Rate limiting is in-memory per process; keep to a single worker (the default).

## 3. Cloudflare Pages frontend

| Setting | Value |
|---|---|
| Framework preset | None (or Vite) |
| Root directory | `frontend` |
| Build command | `npm run build` |
| Build output directory | `dist` |
| Environment variable | `VITE_API_URL` = the Render backend's public HTTPS URL |

`VITE_API_URL` is baked in at build time, so changing it requires a rebuild.

**[verify on first deploy] Deep links.** Open `https://<pages-url>/track` directly and press refresh.
The app uses client-side routing; Pages is documented to treat a project with no top-level
`404.html` as a single-page app, and the project has none. If a direct visit 404s, add a file
`frontend/public/_redirects` containing `/* /index.html 200` and redeploy.

## 4. CORS, cookies and domain (read this before testing login)

Authentication uses an httpOnly session cookie plus a CSRF cookie with `SameSite=Lax`.

- It works when the frontend and backend share a **registrable domain**:
  `www.example.com` + `api.example.com`.
- It will **silently fail** (you appear logged out right after signing in) when they are on unrelated
  domains - which is exactly what happens with the default `*.pages.dev` + `*.onrender.com` URLs.
  Those defaults are fine to test public pages, tracking, quote and contact forms, but **do not
  expect login to work until both sit under one domain you control.**
- If you can only ever use two unrelated domains, set `COOKIE_SAMESITE=none` (with
  `COOKIE_SECURE=true`); the CSRF double-submit check remains in force.

When the real domain is known, change exactly these:

| Where | Variable | New value |
|---|---|---|
| Render | `FRONTEND_URL` | `https://www.<domain>` |
| Render | `CORS_ORIGINS` | `https://www.<domain>` |
| Render | `API_URL` | `https://api.<domain>` |
| Render | `COOKIE_DOMAIN` | leave blank unless you deliberately share cookies across subdomains |
| Cloudflare Pages | `VITE_API_URL` | `https://api.<domain>` (then redeploy) |

Attach `www.<domain>` to Pages and `api.<domain>` to the Render service (both via each dashboard's
"custom domain" setting plus the DNS records they show you).

## 5. Migrations

```
alembic upgrade head
```

Runs automatically at the start of the Render start command on every deploy. Run by hand (from
`backend/`, with `DATABASE_URL` set) if you ever need to. Never drop or recreate the production
database to change schema.

## 6. Create the first admin

There is no public "become admin" route. From a Render shell (or locally with `DATABASE_URL`
pointing at Neon):

```
cd backend
python scripts/create_admin.py --email you@yourcompany.com --name "Your Name"
```

It prompts for the password and creates exactly one SUPER_ADMIN. **Never run `seed_dev.py` in
production** - it creates demo shipments and demo accounts (it refuses if `ENVIRONMENT=production`).

## 7. Health checks

- `GET /health` - process is up
- `GET /health/db` - database reachable (returns 503 if not)

## 8. First live test checklist

1. `/health` and `/health/db` return ok.
2. `/docs` loads (API documentation).
3. Home, About, Services, FAQ, Locations, Careers, Legal pages load; switch language.
4. Track a real tracking number; an unknown number shows "not found".
5. Submit a quote and a contact message; see them under Staff -> Quotes/Messages.
6. Register a customer, sign in, sign out (needs the shared-domain setup in section 4).
7. Sign in as the admin, create a shipment, add a tracking event, confirm the public tracking page updates.
8. Forgot password: needs working email (see the SMTP limitation above).

## 9. Local development (native, no Docker)

Requires Python 3.12+, Node 20+, PostgreSQL 14+ installed natively.

```
# database (once)
psql -U postgres -c "CREATE USER tnt WITH PASSWORD 'tnt_dev_pw' CREATEDB;"
psql -U postgres -c "CREATE DATABASE tnt_dev OWNER tnt;"
psql -U postgres -c "CREATE DATABASE tnt_test OWNER tnt;"

# backend
cd backend && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
alembic upgrade head
ENVIRONMENT=development python scripts/seed_dev.py   # optional demo data
uvicorn app.main:app --reload

# frontend (second terminal)
cd frontend && npm install && cp .env.example .env && npm run dev
```

## 10. Rollback

- App: Render keeps previous deploys - use "Rollback" on the service.
- Schema: `alembic downgrade -1` reverts the latest migration (test on staging first; the initial
  migration's downgrade drops tables).

## 11. Environment variable reference

Full list with defaults: `backend/.env.example` and `frontend/.env.example`. Never commit a filled-in `.env`.
