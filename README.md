<div align="center">

# NeuroBloom

**Cognitive training & clinical monitoring platform for neurological rehabilitation**

[![Live Demo](https://img.shields.io/badge/Live%20Demo-neurobloom--67qo.onrender.com-0e7490?style=for-the-badge&logo=render)](https://neurobloom-67qo.onrender.com)
[![Backend](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![Frontend](https://img.shields.io/badge/Frontend-SvelteKit-FF3E00?style=flat-square&logo=svelte)](https://kit.svelte.dev)
[![Database](https://img.shields.io/badge/Database-PostgreSQL-4169E1?style=flat-square&logo=postgresql)](https://www.postgresql.org)

</div>

---

## Overview

NeuroBloom is a full-stack clinical web application designed for patients with neurological conditions (e.g. Multiple Sclerosis, Mild Cognitive Impairment, Post-COVID syndrome) and their treating clinicians. It provides:

- **Patients** — a structured daily cognitive training programme with adaptive difficulty, progress tracking, and prescription management
- **Doctors** — a clinical portal with patient assignment, analytics, digital prescriptions, progress reports, and risk alerts
- **Admins** — a hospital-level management console for doctors, departments, patients, audit logs, and system health

---

## Live Demo

| URL | Description |
|-----|-------------|
| **[https://neurobloom-67qo.onrender.com](https://neurobloom-67qo.onrender.com)** | Production deployment (Render) |
| `https://neurobloom-67qo.onrender.com/api/docs` | Interactive API docs (Swagger UI) |

> **Note:** The Render free tier spins down after inactivity. The first request may take 30–60 seconds to wake the service.

### Demo credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | `admin@gmail.com` | `admin123` |
| Doctor | `dr.samira.rahman@gmail.com` | `Doctor123!` |
| Patient | `alice.tan@patient.com` | `Patient123!` |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend API | FastAPI 0.128, Python 3.12 |
| ORM / Models | SQLModel 0.0.31 |
| Database | PostgreSQL 16 |
| Auth | bcrypt password hashing |
| PDF generation | ReportLab 4.4 |
| Frontend | SvelteKit 2, Svelte 5, Vite 5 |
| HTTP client | Axios |
| Charts | Chart.js, Canvas 2D API |
| Localisation | English + Bengali (বাংলা) built-in |
| Container | Docker + Docker Compose |
| Web server | Nginx (production) |
| CI | GitHub Actions (vitest + pytest) |

---

## Project Structure

```
NeuroBloom/
├── backend/                    # FastAPI application
│   ├── app/
│   │   ├── api/                # Route handlers
│   │   │   ├── auth.py         # Patient registration & login
│   │   │   ├── admin.py        # Admin portal endpoints
│   │   │   ├── doctor.py       # Doctor portal endpoints
│   │   │   ├── training.py     # Training plans & sessions
│   │   │   ├── baseline.py     # Baseline cognitive assessment
│   │   │   ├── tasks.py        # Cognitive task library
│   │   │   ├── advanced_analytics.py
│   │   │   └── patient_journey.py
│   │   ├── core/
│   │   │   ├── config.py       # Settings, DB engine, init_db
│   │   │   ├── security.py     # Password hashing
│   │   │   └── prescriptions.py # ReportLab PDF builder
│   │   ├── models/             # SQLModel table definitions
│   │   └── main.py             # FastAPI app + CORS + router mounts
│   ├── tests/                  # pytest integration tests
│   │   ├── conftest.py
│   │   ├── test_auth.py
│   │   └── test_doctor.py
│   ├── seed_initial_data.py    # Admin + departments + tasks
│   ├── seed_departments_demo.py # Demo doctors & patients
│   ├── seed_samira_patients.py  # Patients for a specific doctor
│   ├── requirements.txt
│   └── Dockerfile
├── frontend-svelte/            # SvelteKit application
│   ├── src/
│   │   ├── routes/
│   │   │   ├── dashboard/      # Patient dashboard
│   │   │   ├── training/       # Cognitive task runner
│   │   │   ├── prescriptions/  # Patient prescription view
│   │   │   ├── progress/       # Patient progress charts
│   │   │   ├── messages/       # Patient–doctor messaging
│   │   │   ├── doctor/         # Doctor portal (dashboard, patients, prescriptions, analytics…)
│   │   │   └── admin/          # Admin portal (doctors, patients, departments, audit logs…)
│   │   └── lib/
│   │       ├── i18n/           # Translation engine (EN + BN)
│   │       ├── components/     # Shared UI components
│   │       └── dashboard/      # Patient dashboard data layer
│   ├── package.json
│   └── Dockerfile
├── compose.yaml                # Docker Compose (db + backend + frontend)
├── .env.example                # Environment variable template
└── .github/workflows/tests.yml # CI pipeline
```

---

## Quick Start (Docker — Recommended)

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (includes Compose)
- Git

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/your-org/NeuroBloom.git
cd NeuroBloom

# 2. Create your local environment file
cp .env.example .env.local
```

Open `.env.local` and set a secure password:

```env
POSTGRES_DB=neurobloom_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-secure-password
POSTGRES_PORT=5432
POSTGRES_HOST=localhost
CORS_ALLOWED_ORIGINS=http://localhost:5174,http://localhost:8080
```

```bash
# 3. Build and start all services
docker compose up --build
```

The application is now running at **http://localhost:8080**.

```bash
# 4. Seed initial data (first run only)
docker compose exec backend python seed_initial_data.py

# 5. (Optional) Seed demo doctors, patients, and department assignments
docker compose exec backend python seed_departments_demo.py
```

---

## Local Development (Without Docker)

### Requirements
- Python 3.12+
- Node.js 20+
- PostgreSQL 16 running locally

### 1 — Environment

```bash
cp .env.example .env.local
# Edit .env.local with your local Postgres credentials
```

### 2 — Backend

```bash
cd backend

# Create and activate a virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the API server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The API will be available at `http://127.0.0.1:8000`.  
Interactive docs: `http://127.0.0.1:8000/docs`

### 3 — Seed the database

Run these from the `backend/` directory with the virtual environment active:

```bash
# Core data: admin account, departments, cognitive task library
python seed_initial_data.py

# Demo data: 8 doctors (4 per department) + 12 patients + assignments
python seed_departments_demo.py
```

### 4 — Frontend

```bash
cd frontend-svelte

npm install

npm run dev
```

The frontend runs at **http://localhost:5174** and proxies all `/api` requests to `http://127.0.0.1:8000`.

---

## Environment Variables

All variables are read from `.env.local` at the repo root (shared by Docker Compose and the backend).

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_DB` | `neurobloom_db` | Database name |
| `POSTGRES_USER` | `postgres` | Database user |
| `POSTGRES_PASSWORD` | *(required)* | Database password |
| `POSTGRES_HOST` | `localhost` | DB host (`db` inside Docker) |
| `POSTGRES_PORT` | `5432` | DB port |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5174,...` | Comma-separated allowed origins |
| `DATABASE_URL` | *(derived)* | Optional full connection string — overrides individual fields |
| `API_BASE_URL` | `http://localhost:8000` | Used for PDF generation links |
| `SQL_ECHO` | `false` | Log all SQL queries |
| `DB_STARTUP_MAX_ATTEMPTS` | `20` | Retries waiting for Postgres |
| `DB_STARTUP_RETRY_SECONDS` | `2` | Seconds between retries |

---

## Running Tests

### Frontend (vitest)

```bash
cd frontend-svelte
npm test
```

### Backend (pytest)

```bash
cd backend
python -m pytest tests/ -v
```

Tests use an in-memory SQLite database and mock the Postgres startup — no running database required.

### CI

Every push and pull request to `main`/`master` runs both test suites via GitHub Actions (`.github/workflows/tests.yml`).

---

## User Roles & Features

### Patient
| Feature | Description |
|---------|-------------|
| Cognitive training | Daily adaptive sessions across 4 domains: Working Memory, Processing Speed, Attention, Cognitive Flexibility |
| Baseline assessment | One-time assessment to calibrate difficulty |
| Progress tracking | Domain scores, trend charts, badges, streaks |
| Prescriptions | View and download clinician-issued PDF prescriptions |
| Messaging | Direct messages with assigned doctor |
| Bilingual UI | Full English + Bengali (বাংলা) interface |

### Doctor
| Feature | Description |
|---------|-------------|
| Patient dashboard | Clinical overview per patient: adherence, risk alerts, domain progress |
| Analytics | Performance trends, cohort statistics |
| Prescriptions | Issue, revise, and generate PDF prescriptions |
| Progress reports | Generate structured PDF reports per patient |
| Messaging | Secure patient communication |
| Interventions | Log and track clinical interventions |

### Admin
| Feature | Description |
|---------|-------------|
| Doctor management | Approve, activate, suspend clinician accounts |
| Patient management | View all patients and their assignment status |
| Department management | Create departments, assign doctors |
| Audit logs | Full action trail for all admin/doctor operations |
| System health | API status, DB connectivity, service uptime |
| Analytics | Platform-wide usage statistics |
| Research data | Anonymised export for research |
| Notification centre | Broadcast notices to doctors or patients |

---

## Cognitive Tasks

| Task | Domain |
|------|--------|
| Dual N-Back | Working Memory |
| Digit Span | Working Memory |
| Spatial Span | Working Memory |
| Letter-Number Sequencing | Working Memory |
| Operation Span | Working Memory |
| Symbol Digit Modalities (SDMT) | Processing Speed |
| Choice Reaction Time | Processing Speed / Attention |
| Inspection Time | Processing Speed |
| PASAT | Processing Speed |
| Pattern Comparison | Processing Speed |
| SART | Attention |
| Stroop | Attention / Flexibility |
| Trail Making A | Attention |
| Rule Shift | Cognitive Flexibility |
| Tower of London | Planning |
| Multiple Object Tracking | Attention |
| Visual Search | Attention |
| Landmark Task | Spatial Cognition |
| Twenty Questions | Planning |
| Category Fluency | Executive Function |

---

## API Overview

All endpoints are under `/api`. Full interactive documentation is available at `/api/docs` when the backend is running.

| Prefix | Module | Description |
|--------|--------|-------------|
| `/api/auth` | `auth.py` | Patient login, registration, prescriptions |
| `/api/training` | `training.py` | Training plans, sessions, task generation & submission |
| `/api/baseline` | `baseline.py` | Baseline assessment |
| `/api/tasks` | `tasks.py` | Cognitive task library |
| `/api/doctor` | `doctor.py` | Doctor portal (patients, analytics, notifications, interventions) |
| `/api/admin` | `admin.py` | Admin portal (doctors, departments, audit logs, analytics) |
| `/api/patient-journey` | `patient_journey.py` | Patient journey tracking |
| `/api/advanced-analytics` | `advanced_analytics.py` | MS research analytics |

---

## Deployment (Render)

The live instance runs on [Render](https://render.com). Environment variables are configured in the Render dashboard under **Environment**:

| Variable | Value |
|----------|-------|
| `DATABASE_URL` | Render internal Postgres URL |
| `CORS_ALLOWED_ORIGINS` | `https://neurobloom-67qo.onrender.com` |
| `API_BASE_URL` | `https://neurobloom-67qo.onrender.com` |

To deploy your own instance:
1. Fork this repository
2. Create a new **Web Service** on Render pointing to the `backend/` directory
3. Create a **Static Site** or another Web Service for the frontend, or use the Docker Compose deployment
4. Add a **PostgreSQL** database and copy the internal connection string to `DATABASE_URL`
5. Run `seed_initial_data.py` via the Render shell after first deploy

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes and run the test suite (`npm test` + `pytest`)
4. Open a pull request — the CI pipeline will run automatically

---

## License

This project is licensed under the terms of the [LICENSE](LICENSE) file in the root of this repository.

