# Stationery Junction

Full-stack e-commerce platform for retail and wholesale stationery — built with **Next.js 14**, **FastAPI**, and optional **Oracle DB** (falls back to JSON file storage).

---

## Architecture

```
Ecommerce app/
├── backend/          FastAPI Python API
├── frontend/
│   ├── src/          Next.js 14 web app (App Router)
│   ├── mobile/       Expo React Native app
│   └── packages/
│       └── api-client/  Shared Axios client (web + mobile)
└── docker-compose.yml
```

| Layer | Stack |
|-------|-------|
| Web frontend | Next.js 14, React 18, TypeScript, Tailwind CSS |
| Mobile | Expo 54, React Native, NativeWind, Zustand |
| Backend API | FastAPI, Pydantic v2, SQLAlchemy 2 async |
| Database | Oracle (optional) or JSON file storage |
| Object storage | Oracle Cloud Infrastructure (OCI) |
| Auth | JWT (access + refresh), HttpOnly cookies, bcrypt |

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (optional, for containerised dev)

---

## Quick Start (Local)

### 1. Backend

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env   # fill in required values (see below)
uvicorn app.main:app --reload --port 8000
```

API docs available at: `http://localhost:8000/docs`

### 2. Frontend (Web)

```bash
cd frontend
npm install
cp .env.local.example .env.local   # or create manually
npm run dev   # runs on http://localhost:3000
```

### 3. Mobile

```bash
cd frontend/mobile
npm install
npx expo start
```

---

## Docker (all services)

```bash
docker compose up --build
```

| Service | URL |
|---------|-----|
| Backend API | http://localhost:8000 |
| Frontend | http://localhost:3000 |
| API Health | http://localhost:8000/api/health |
| API Docs | http://localhost:8000/docs |

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `JWT_SECRET_KEY` | ✅ | Secret for signing access tokens |
| `JWT_REFRESH_SECRET_KEY` | ✅ | Secret for refresh tokens |
| `ALLOWED_ORIGINS` | ✅ | Comma-separated CORS origins |
| `ENVIRONMENT` | | `development` or `production` |
| `DATABASE_URL` | | Oracle connection string (omit to use JSON storage) |
| `OCI_BUCKET_NAME` | | OCI object storage bucket |
| `OCI_NAMESPACE` | | OCI namespace |
| `OCI_REGION` | | OCI region (e.g. `ap-hyderabad-1`) |
| `OCI_USER_OCID` | | OCI user OCID |
| `OCI_TENANCY_OCID` | | OCI tenancy OCID |
| `OCI_FINGERPRINT` | | OCI API key fingerprint |
| `OCI_PRIVATE_KEY` | | OCI private key (PEM, newlines as `\n`) |
| `SMTP_HOST` | | SMTP server for error alert emails |
| `SMTP_PORT` | | SMTP port (default 587) |
| `SMTP_USER` | | SMTP username |
| `SMTP_PASSWORD` | | SMTP password |
| `SLOW_REQUEST_THRESHOLD_MS` | | Log warning if request exceeds this (default 500) |
| `SENTRY_DSN` | | Sentry DSN for error tracking; leave empty to disable |

### Frontend (`frontend/.env.local`)

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Backend API base URL (default: `http://localhost:8000/api`) |
| `NEXT_PUBLIC_SITE_URL` | Public site URL for canonical/sitemap (default: `https://www.stationeryjunction.com`) |
| `NEXT_PUBLIC_GTM_ID` | Google Tag Manager ID |
| `NEXT_PUBLIC_GA_ID` | Google Analytics measurement ID |
| `NEXT_PUBLIC_CLARITY_ID` | Microsoft Clarity project ID |
| `NEXT_PUBLIC_SOCIAL_INSTAGRAM` | Instagram profile URL (for Organization JSON-LD) |
| `NEXT_PUBLIC_SOCIAL_FACEBOOK` | Facebook page URL |
| `NEXT_PUBLIC_SOCIAL_TWITTER` | Twitter/X profile URL |

---

## Running Tests

### Backend

```bash
cd backend
pytest tests/ -v
# With coverage:
pytest tests/ --cov=app --cov-report=term-missing
```

### Frontend

```bash
cd frontend
npm test              # unit tests (Jest)
npm run test:e2e      # end-to-end (Playwright — requires app running on :3000)
```

---

## Code Quality

### Backend (Python)

```bash
cd backend
ruff check app/       # lint
ruff format app/      # format
```

### Frontend (TypeScript)

```bash
cd frontend
npm run lint          # ESLint
npm run format        # Prettier
npm run format:check  # Check without writing
```

### Pre-commit (all at once)

```bash
pip install pre-commit
pre-commit install     # installs git hooks
pre-commit run --all-files  # run manually
```

---

## Key Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check (DB probe + uptime) |
| GET | `/metrics` | Prometheus metrics |
| GET | `/docs` | Swagger UI |
| POST | `/api/auth/login` | Login |
| GET | `/api/products/public` | Public product catalogue |
| POST | `/api/orders/` | Place an order |
| GET | `/api/analytics/kpi` | Admin KPIs |

---

## CI/CD

GitHub Actions runs on every push to `main` / `develop`:

- **backend-tests** — `pytest` with coverage upload to Codecov
- **frontend-tests** — Jest with coverage upload to Codecov
- **lint** — Ruff (Python) + ESLint (TypeScript)

Dependabot is configured for `pip`, `npm`, and GitHub Actions dependencies.
