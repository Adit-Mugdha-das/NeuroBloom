
# NeuroBloom

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23496185.svg)](https://doi.org/10.5281/zenodo.23496185)

NeuroBloom is an open-source research software prototype for studying longitudinal cognitive-task records and clinician-supervised rehabilitation workflows in multiple sclerosis. It includes original task implementations and descriptive analytics whose psychometric and clinical validity has not been established. The current release is intended only for isolated demonstrations using synthetic data.

A synthetic-data demonstration instance is available at https://neurobloom-67qo.onrender.com/. Do not enter real patient data; see [Security and Intended Use](#security-and-intended-use).

## Key Features

- 35 cognitive tasks across 6 cognitive domains, each with 10 difficulty levels
- Pre-session contextual capture for fatigue, sleep quality, stress, and medication timing
- Descriptive longitudinal indicators supporting future digital-biomarker-oriented research
- Three-role architecture for patients, clinicians, and administrators
- Bilingual support in Bengali and English
- Rule-based review flags for clinician interpretation and bidirectional messaging
- Free-of-cost and open source under the MIT License

## System Requirements

For manual installation:

- Python 3.10+
- Node.js 18+
- npm
- PostgreSQL 14+
- Modern web browser

For Docker-based deployment, Docker and Docker Compose are required.

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/Adit-Mugdha-das/NeuroBloom.git
cd NeuroBloom
```

To reproduce the software version cited in the manuscript, check out the archived release:

```bash
git checkout v1.2.2
```

### 2. Set up the backend

```bash
cd backend
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure the environment

Return to the repository root and copy the environment template:

```bash
cd ..

# Windows PowerShell
Copy-Item .env.example .env.local

# macOS / Linux
cp .env.example .env.local
```

Edit `.env.local` with the local PostgreSQL database name, username, password, host, port, and allowed frontend origins.

Set `JWT_SECRET_KEY` in `.env.local` to a long random value (at least 32 characters) so that sign-in sessions survive a backend restart:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

If it is not set, the backend generates a temporary key at start-up and every session ends when the backend restarts. See [Security and Intended Use](#security-and-intended-use) for the session and cookie settings.

For local development without Docker, ensure PostgreSQL is running and the configured database exists before starting the backend. Leave `DATABASE_URL` commented unless you intentionally want to override the individual PostgreSQL settings.

If necessary, create the database:

```bash
createdb neurobloom_db
```

Alternatively, using `psql`:

```bash
psql -U postgres -c "CREATE DATABASE neurobloom_db;"
```

### 4. Initialize the database

```bash
cd backend
python seed_initial_data.py
```

### 5. Start the backend API

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 6. Start the frontend

Open another terminal and navigate to the frontend directory:

```bash
cd frontend-svelte
npm install
npm run dev
```

The frontend development server runs at `http://localhost:5174`, and the backend API runs at `http://127.0.0.1:8000`.

## Running with Docker

Docker Compose is the recommended setup for local deployment. It starts PostgreSQL, the FastAPI backend, and the Svelte frontend.

From the repository root:

```bash
# Windows PowerShell
Copy-Item .env.example .env.local

# macOS / Linux
cp .env.example .env.local

docker compose --env-file .env.local -f compose.yaml up --build
```

If `.env.local` already exists, reuse it instead of overwriting it.

Once the containers are running, initialize the default administrator account and reference data:

```bash
docker compose --env-file .env.local -f compose.yaml exec backend python seed_initial_data.py
```

The application is available at:

- Frontend: `http://localhost:8080`
- Backend API: `http://localhost:8000`

If your Docker installation uses the older standalone Compose binary, replace `docker compose` with `docker-compose`.

## Reproducing the Manuscript Demonstration

The following procedure reproduces the synthetic-data demonstration, sensitivity analyses, and six-session example described in the SoftwareX manuscript.

The deployment uses Docker Compose with Python 3.12, Node.js 20, and PostgreSQL 16 inside the containers. Only Docker and Docker Compose are required on the host.

Run the commands from the repository root using the version-specific source code (`v1.2.2`).

### 1. Start the application

Create `.env.local` from `.env.example` if it does not already exist, then run:

```bash
docker compose --env-file .env.local -f compose.yaml up --build -d
```

### 2. Initialize the database

Initialize the database and cognitive-task library:

```bash
docker compose --env-file .env.local -f compose.yaml exec backend python seed_initial_data.py
```

This step is required only once for a new database.

### 3. Generate synthetic demonstration data

```bash
docker compose --env-file .env.local -f compose.yaml exec backend python scripts/seed_demo_clinical_data.py
```

The script generates:

- 8 synthetic clinicians and 8 synthetic patients
- Patient–clinician assignments
- Baseline assessments and training plans
- 60 training sessions with contextual records
- Progress reports, prescriptions, and messages
- Review flags and longitudinal performance records

The script prints the demonstration accounts it creates. Running it again replaces the previous demonstration records.

A fixed random seed is used to reproduce the same synthetic patient profiles and performance values. However, record dates are generated relative to the execution date, so dashboards based on recent activity may differ between runs.

### 4. Explore the patient–clinician workflow

Open:

`http://localhost:8080`

Use the following local demonstration accounts:

| Role | Email | Password |
|---|---|---|
| Clinician | `dr.samira.rahman@demo.neurobloom.example` | `doctor1234` |
| Patient | `sharmin.akter@demo.neurobloom.example` | `patient1234` |

The patient interface provides access to the baseline assessment, training sessions, contextual information, and progress history.

The clinician interface shows the assigned patient's baseline results, session history, longitudinal trends, and descriptive analytics.

These accounts are intended for isolated local demonstration only.

### 5. Reproduce the analytics and sensitivity results

Run the following scripts:

```bash
docker compose --env-file .env.local -f compose.yaml exec backend python scripts/fatigue_proxy_sensitivity.py

docker compose --env-file .env.local -f compose.yaml exec backend python scripts/trend_sensitivity.py

docker compose --env-file .env.local -f compose.yaml exec backend python scripts/illustrative_case.py
```

The scripts reproduce:

- Fatigue-proxy parameter sensitivity
- EWMA and trend-classification sensitivity
- The six-session synthetic longitudinal example

The first two scripts reproduce the sensitivity results in Supplementary Table S3. The final script reproduces the synthetic case presented in the manuscript.

Each script prints its results and writes a JSON file to `analysis/results/` within the backend container.

To copy the generated results to the host:

```bash
docker compose --env-file .env.local -f compose.yaml cp backend:/app/analysis/results/. backend/analysis/results
```

The files will be available in `backend/analysis/results/`.

Without Docker, the scripts can also be executed from the `backend` directory using:

```bash
python scripts/fatigue_proxy_sensitivity.py
python scripts/trend_sensitivity.py
python scripts/illustrative_case.py
```

The generated results demonstrate numerical software behaviour using synthetic data. They do not establish clinical validity or associations in real patients.

### Tested Deployment Environment

Two records apply. The October 2026 record is the authors' manual reproduction of the demonstration workflow. The 25 November 2026 record is a clean installation that followed only the steps above, with the automated tests run against the running containers.

| Component | Manual reproduction (October 2026, authors' record) | Clean installation and automated tests (25 November 2026) |
|---|---|---|
| Host operating system | Windows 10 Pro, build 19045 | Windows 10 Pro, build 19045 |
| Docker | Docker Desktop, Docker 29.2.0 | Docker Desktop, Docker 29.2.0 |
| Docker Compose | v5.0.2 | v5.0.2 |
| Backend container | Python 3.12 | Python 3.12 (`python:3.12-slim`) |
| Frontend container | Node.js 20 | Node.js 20 build (`node:20-alpine`), served by nginx 1.27 |
| Database container | PostgreSQL 16 | PostgreSQL 16 (`postgres:16-alpine`) |
| Browser | Google Chrome 151.0.7922.138 and Microsoft Edge 154.0.4258.37, used manually | Chromium 131.0.6778.33 (Playwright 1.49.1, headless), automated tests only |

In the November check the synthetic dataset was generated as described (8 clinicians, 8 patients, 60 training sessions with contextual records, 8 progress reports, 4 prescriptions), the three analysis scripts reproduced `backend/analysis/results/` byte for byte, and the 14 browser end-to-end tests passed against the running containers. The only deviation was the frontend host port (8081 instead of 8080, with the matching CORS origin), because port 8080 was occupied by another service on that machine.

The automated suites also run in GitHub Actions on Ubuntu (`ubuntu-latest`) with Python 3.12, Node.js 20, PostgreSQL 16 and Playwright Chromium; all four jobs passed for the revision containing the authentication changes. Local test runs used Python 3.13 and Node.js 22.

Not tested: macOS and Linux hosts for the Docker deployment, Firefox and Safari, current Chrome and Edge releases other than those listed, mobile browsers, and the hosted demonstration instance. Other operating systems and dependency versions may work but are not covered by these records.

## Training Plan and Analytics Rules

These are developer-chosen rules. They have not been empirically optimised or clinically validated.

### Focus areas and rebalancing

- **New plan.** A training plan is created from the baseline assessment. The six domains are ranked by baseline score: the two weakest become primary focus, the next two secondary focus and the two strongest maintenance. Each session has four tasks, one from each primary and secondary domain; maintenance domains are not trained in sessions.
- **Automatic rebalancing.** After every fourth completed session (a session is complete when all four of its tasks are submitted) all six domains are ranked again, weakest first. A domain's value is the mean score of its results among the plan's 12 most recent task results; a domain with no result in that window (normally a maintenance domain) keeps its baseline score. The two weakest become primary, the next two secondary and the two strongest maintenance, so a maintenance domain can return to focus and every domain always has a role. Ties keep the order working memory, attention, flexibility, planning, processing speed, visual scanning. Every submitted task result counts, including a repeated attempt at the same task slot.
- **Clinician-selected focus areas.** When an assigned clinician (with the patient's consent) sets the focus areas, automatic rebalancing stops for that training plan and the clinician's selection is kept until the clinician changes it. A new training plan, created from a new baseline assessment, starts again from the baseline ranking with automatic rebalancing.

### Difficulty adjustment

- **Initial level** (per domain, from the baseline score): below 50, level 2; 50–69, level 4; 70–84, level 7; 85 or above, level 9.
- **Generic submission route** (`/api/training/training-session/submit`): when a session is completed, each of its four results changes the level of its domain by accuracy alone: at least 85% raises it by one, below 65% lowers it by one, otherwise it is unchanged.
- **Task-specific routes** (`/api/training/tasks/<task>/submit/...`): the level changes after each task, using that task's own measures and thresholds (for example accuracy, span or composite scores, error counts or false alarms). Most tasks change by at most one level; Stroop, Flanker, Go/No-Go, Cancellation Test, Category Fluency and Twenty Questions can change by two.
- Levels always stay within 1–10.

### Trend labels

The score and reaction-time trends use an exponentially weighted moving average (α = 0.2) and the slope of its five most recent points, relative to the series mean (±1% threshold). A trend label (improving, declining or stable) is assigned only when at least **three** valid session values are available; with fewer, the API returns `insufficient_data` and the interface shows "Insufficient data", while the EWMA value itself is still shown.

### Analytics configuration

- `backend/config/analytics.json` holds the fatigue-proxy parameters: component weights, normalisation scales, the minimum number of trials and the minimum observations per quartile. The EWMA smoothing constant, window, threshold and three-value minimum are defaults in `backend/app/core/advanced_analytics.py`.
- The longitudinal indicators (fatigue proxy, reaction-time CV, EWMA trends, within-person standardized change and contextual correlations) are not stored. Each request recalculates them from the stored trial and session records with the configuration in place at that moment, so after a configuration change all indicators, including those for earlier sessions, are recalculated with the new values.
- Indicator outputs do not record which configuration produced them. Keep a copy of `analytics.json` with any exported or reported indicator values. Saved progress reports store summary scores and domain statistics, not these indicators.

## Software Testing and Continuous Integration

NeuroBloom includes automated backend, frontend and browser tests. They check software behaviour, access control and the consistency of recorded outputs; they do not establish the psychometric or clinical validity of the cognitive tasks.

### Test suites

| Suite | Tool | Tests | Database |
|---|---|---|---|
| Backend unit and API tests | pytest | 349 collected (343 run, 6 skipped) | In-memory SQLite by default; PostgreSQL 16 in CI |
| Frontend unit tests | Vitest | 36 | — |
| Browser end-to-end tests | Playwright (Chromium) | 14 | PostgreSQL 16 |

**Backend.** 121 tests cover numerical scoring, trial generation, response classification, difficulty adjustment, the task inventory, analytics, API endpoints, focus rebalancing (including maintenance domains and clinician-selected focus areas), the three-session minimum for trend labels and missing-data handling, including an API-level patient–clinician integration test. The authentication and authorization suite (`backend/tests/test_security_access_control.py`) adds 228 tests:

- 189 parametrised checks, one per API route and method, that requests without a valid session are refused (the 6 public routes — registration, sign-in and sign-out — are skipped);
- 39 scenario tests covering login tokens and the httpOnly cookie, `/api/auth/me` and logout, expired, forged and malformed tokens, password resets, deactivated and suspended accounts, the cross-site request forgery header, role separation (including colliding patient, clinician and administrator ids), binding of every user, patient, clinician and administrator identifier to the signed-in account, ownership of messages, prescriptions, reports, assignment requests, training sessions, session contexts and training plans, consent withdrawal and restoration, consent being changed only by the patient (a clinician's approval cannot turn it back on), immediate loss of access when an assignment ends, separation of the administrator role, and authenticated session completion with result persistence.

The integration test now signs in each actor through the real login endpoints and confirms that an unassigned clinician, signed in with its own session, is refused — including when it supplies the assigned clinician's identifier.

**Browser end-to-end tests** (`frontend-svelte/e2e/`) run against a PostgreSQL-backed backend loaded with the synthetic demonstration data:

- sign-in, the httpOnly session cookie (no token visible to page scripts or stored in the browser), logout, wrong passwords, expired or tampered sessions, and redirection of visitors without a session;
- a patient cannot read another patient's records, even after editing the profile saved in the browser; patient sessions cannot use clinician or administrator endpoints; clinicians cannot open patients assigned to someone else;
- a patient completes a task (Pattern Comparison) in the browser, and the stored result appears in the patient's history and in the assigned clinician's session list;
- a clinician reviews an assigned patient, loses access while the patient's consent is withdrawn, and regains it when consent is restored;
- administrators can only use admin data as themselves;
- every patient page — including the 31 training task pages and the 6 baseline task pages, which together host all 35 tasks — and every clinician and administrator page loads without any refused (401/403) or failed (5xx) API call. (Four baseline tasks — Simple Reaction Time, N-Back, Continuous Performance and Task Switching — share their training page with Choice Reaction Time, Dual N-Back, Go/No-Go and Rule Shift; see `docs/task_inventory.csv`.)

### Results at the time of revision (25 November 2026)

| Metric | Result |
|---|---|
| Backend tests, SQLite | 343 passed, 6 skipped |
| Backend tests, PostgreSQL 16 | 343 passed, 6 skipped |
| Frontend unit tests | 36 passed |
| Browser end-to-end tests | 14 passed |
| Backend line coverage (application package) | 49% (about 40% before this revision) |
| Frontend unit-test line coverage | 14.5% of the application source (`src/`) |

The backend coverage of the access-control module (`app/core/access_control.py`) is 94%. Coverage figures describe this run, not a measurement of every later commit.

### Running backend tests

From the repository root:

```bash
cd backend

pip install -r requirements.txt
pip install pytest pytest-httpx pytest-cov

pytest tests/ -v --tb=short --cov=app --cov-report=term
```

By default each test uses an isolated in-memory SQLite database, so no PostgreSQL server is needed. To run the same suite against PostgreSQL, point `TEST_DATABASE_URL` at an empty test database (it is emptied before every test):

```bash
docker run -d --name neurobloom-test-db -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=neurobloom_test -p 5433:5432 postgres:16-alpine

TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5433/neurobloom_test pytest tests/ -v --tb=short
```

### Running frontend unit tests

```bash
cd frontend-svelte

npm ci
npm run test:coverage
```

### Running browser end-to-end tests

The browser tests need a backend with the synthetic demonstration data and a frontend build that points at it. Use a dedicated database: the tests sign in as demonstration accounts and add task results.

```bash
# 1. Backend (from backend/), with an empty PostgreSQL database
export DATABASE_URL=postgresql://postgres:postgres@localhost:5434/neurobloom_e2e
export JWT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(64))")
export CORS_ALLOWED_ORIGINS=http://localhost:5173
uvicorn app.main:app --host 127.0.0.1 --port 8000 &
python seed_initial_data.py
python scripts/seed_demo_clinical_data.py

# 2. Frontend (from frontend-svelte/)
npx playwright install chromium
VITE_API_BASE_URL=http://localhost:8000 npm run build
npm run test:e2e
```

Playwright serves the built frontend at `http://localhost:5173` and uses the API at `E2E_API_URL` (default `http://localhost:8000`).

### GitHub Actions

Continuous integration is configured in `.github/workflows/tests.yml` and runs on pushes and pull requests to `main` or `master`:

| Job | What it runs |
|---|---|
| Frontend Unit Tests | Vitest with coverage (Node.js 20) |
| Backend API Tests | pytest with coverage on in-memory SQLite (Python 3.12) |
| Backend API Tests (PostgreSQL) | the same pytest suite against a PostgreSQL 16 service |
| Browser End-to-End Tests | Playwright (Chromium) against the backend on PostgreSQL 16, loaded with the synthetic demonstration data |

### Testing limitations

- Frontend unit tests cover scoring and workflow modules; Svelte page components are exercised by the browser tests rather than by unit tests, so frontend unit-test line coverage remains low.
- The browser tests complete one task (Pattern Comparison) end to end; the other task pages are opened and loaded but not completed in the browser. Completion of a full four-task session is verified at the API level.
- Browser tests run in Chromium only.
- Coverage of the large training and clinician routers remains partial.
- No load testing, penetration testing or formal security audit has been carried out.

## API Documentation

NeuroBloom provides automatically generated OpenAPI documentation through FastAPI.

After starting the backend:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

These interfaces document the available API endpoints, request parameters, and response schemas.

## Project Structure

```text
NeuroBloom/
|-- backend/                 # FastAPI backend, models, APIs, services, and scripts
|-- frontend-svelte/         # SvelteKit frontend
|-- Paper_Materials/         # SoftwareX manuscript and publication materials
|-- .github/workflows/       # Continuous integration workflows
|-- compose.yaml             # Docker Compose configuration
|-- .env.example             # Environment variable template
|-- CITATION.cff             # Software citation metadata
|-- LICENSE                  # MIT License
`-- README.md                # Project documentation
```

## User Roles

**Patients:** Complete baseline assessments and cognitive training tasks, submit contextual information, review progress, receive prescriptions, and communicate with clinicians.

**Clinicians:** Review patient histories, monitor longitudinal trends and review flags, adjust rehabilitation plans, issue prescriptions, generate reports, and communicate with assigned patients.

**Administrators:** Manage users, departments, assignments, notifications, audit logs, system health, and research-oriented data exports.

## Security and Intended Use

NeuroBloom is a research software prototype intended for isolated demonstrations using synthetic data. Do not enter real patient information. The sign-in and registration pages show this notice.

### Implemented security controls

- **Passwords** are stored as bcrypt hashes.
- **Authentication.** Patient, clinician and administrator sign-in issues a signed JSON Web Token (HS256, PyJWT) that expires after 8 hours by default (`ACCESS_TOKEN_EXPIRE_MINUTES`). The token names the account and its role and carries a fingerprint of the stored password hash, so changing or resetting a password ends existing sessions. On every request the server loads the account again: deactivated patients and administrators, and suspended or unverified clinicians, are refused immediately.
- **Token storage in the browser.** The token is delivered only as an httpOnly cookie (`neurobloom_session`, `SameSite=Lax` by default, `Secure` when configured), so page scripts cannot read it. localStorage and sessionStorage were rejected because any injected script can read them, and in-memory storage because every page refresh would sign the user out. The browser keeps only a non-secret display profile (id, role, name); the server never trusts it and resynchronises it from `/api/auth/me`. API clients may send the same token as `Authorization: Bearer`.
- **Cross-site request forgery.** Requests that change data and are authenticated by the cookie must carry the header `X-Requested-With: NeuroBloom`; other sites cannot add it because CORS only admits the configured origins.
- **Role-based authorization on the server.** Every API endpoint except registration, sign-in and sign-out requires a valid session. Every user, patient, clinician or administrator identifier in a request must belong to the signed-in account of the matching role; patients act only on their own records, clinicians only as themselves, administrators only through the admin endpoints and only as themselves.
- **Resource ownership.** Messages, prescriptions, progress reports, assignment requests, training sessions, session contexts and training plans are checked against their owner, not only against the identifier in the URL. Patients can message only their assigned clinician and clinicians only their assigned patients. A clinician can add a patient directly only if that patient has requested that clinician.
- **Consent.** Consent to share data with clinicians is a single setting per patient, changed only by the patient: it is turned on when the patient requests a clinician (the request form says so) and can be switched off or on at any time in Settings. A clinician's approval never changes it, so a withdrawal made while a request is pending stays in force. A clinician sees or acts on a patient's data — overview, sessions, trends, progress monitoring, the patient's analytics, interventions, prescriptions, reports, training-plan and focus changes — only while the assignment is active **and** the patient consents. Withdrawing consent or ending the assignment takes effect on the next request, including for sessions that are already signed in. Without consent the assigned patient stays in the clinician's patient list (name, email, diagnosis and treatment goal from the assignment) without activity or baseline status, and is excluded from the clinician's cohort analytics and prescription directory. Messaging between the patient and the assigned clinician, and unassignment, remain available because they do not disclose training data.
- **Logging.** Sign-in no longer writes email addresses or account lists to the server log. Selected administrative actions and research-data exports are recorded in the audit log.

These controls are covered by the authentication and authorization tests described under [Software Testing and Continuous Integration](#software-testing-and-continuous-integration).

### Administrator permissions

Administrators sign in separately and can use only the admin endpoints, and only as themselves; an administrator session is refused on patient and clinician endpoints. Through the admin endpoints an administrator can:

- view platform statistics, review flags, system health and the audit log;
- list patients and clinicians with identifying details (name, email, date of birth, diagnosis, consent status), and open a patient's overview with the assigned clinician, training summary, review priority, recent sessions and progress reports;
- read the full text of patient–clinician messages (message audit) and the list of clinician interventions;
- approve, suspend and reactivate clinicians, deactivate and reactivate patients, reset patient and clinician passwords, and transfer a patient to another clinician;
- manage departments and platform notifications;
- export research datasets in which patients are identified by a pseudonym.

These administrator permissions do not depend on the patient's consent setting, which governs clinician access only. A transfer assigns a new clinician without a request from the patient; that clinician can see the patient's data only if the patient's consent is on. A password reset lets the administrator sign in as that account. Selected administrator actions are written to the audit log; clinician and patient data access is not.

### Session tokens: when they stop working

| Event | Effect on existing sessions |
|---|---|
| Token reaches its expiry time (default 8 hours after sign-in) | Refused |
| Password changed or reset | Refused immediately |
| Account deactivated (patient or administrator) or clinician suspended | Refused immediately, for as long as the account stays deactivated |
| Account reactivated before the token's expiry | The earlier token works again |
| Signing key (`JWT_SECRET_KEY`) changed, or backend restarted without a fixed key | All sessions refused |
| Sign-out | The browser's cookie is cleared; a copy of the token taken earlier remains valid until it expires |
| Consent withdrawn or assignment ended | The session stays valid, but the clinician's access to that patient is refused on the next request |

### Deployment settings

| Setting | Purpose |
|---|---|
| `JWT_SECRET_KEY` | Token signing key, at least 32 characters. Required for any shared deployment; if unset, a temporary key is generated and sessions end on restart. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Session lifetime (default 480). |
| `AUTH_COOKIE_SECURE` | Set to `true` whenever the application is served over HTTPS. |
| `AUTH_COOKIE_SAMESITE` | `lax` (default) when the frontend and API share a site, e.g. `localhost:8080` and `localhost:8000`. Use `none` (requires `AUTH_COOKIE_SECURE=true`) only when they are on different sites; browsers that block third-party cookies may then refuse the session, so serving both from the same site is preferred. |
| `CORS_ALLOWED_ORIGINS` | Must list the exact origin of the frontend. |

### Remaining limitations

The software has not undergone a formal security audit or penetration test, and it must not be used with real patient data or sensitive multi-user records. In particular:

- Tokens are stateless (see the table above). There is no server-side revocation list, so a copied token cannot be cancelled individually before it expires; only a password change, deactivation or a new signing key stops it. There is no refresh-token mechanism.
- There is no rate limiting or lockout after repeated failed sign-ins, no multi-factor authentication and no password-strength policy.
- Stored records have no additional field-level encryption; protection in transit depends on HTTPS configured at deployment.
- Administrators have broad access to identifiable records and message content independent of patient consent (see above), and access by clinicians and patients is not audit-logged.
- Research-export pseudonyms are derived from the account id and email with a fixed text and no secret key, so anyone who knows a patient's id and email can link that patient to the export. The exports are pseudonymised, not anonymised.
- The developer tools (`/api/training/dev/*`, used by the in-app development panel) let a signed-in patient generate or clear synthetic sessions in their own record; they should be disabled in any non-demonstration deployment.
- The demonstration accounts and the default administrator account use fixed, published passwords for local testing. They must not be used in production.
- The httpOnly cookie prevents page scripts from reading the token, but a script injected into the page (cross-site scripting) could still send requests with the user's session while the page is open. No dedicated cross-site scripting review or Content Security Policy is in place.
- The access-control rules are verified by the automated tests described above, not by an independent review.
- The public demonstration instance linked at the top of this README is deployed separately. Until it is redeployed from this version with the settings under [Deployment settings](#deployment-settings), it may not include these controls.

The cognitive tasks are NeuroBloom-specific implementations inspired by established cognitive paradigms. They are not equivalent to standardized clinical instruments, and their psychometric and clinical validity has not been established.

The longitudinal indicators are descriptive engineering measures, not validated diagnostic biomarkers or clinical decision-making tools.

## Tech Stack

- Python
- FastAPI
- SQLModel
- PostgreSQL
- JavaScript
- Svelte
- SvelteKit
- Vite
- Docker and Docker Compose
- pytest and Vitest
- GitHub Actions

## License

NeuroBloom is released under the MIT License. See [LICENSE](LICENSE) for details.

## Citation

If you use NeuroBloom in your research, please cite the archived software release:

> Das, A. M., Deb Nath, A., Alam, K. S., & Hossain, S. I. (2026). *NeuroBloom v1.2.2 – SoftwareX Revision Release* (Version v1.2.2) [Computer software]. Zenodo. https://doi.org/10.5281/zenodo.23496185

**Version:** v1.2.2

**Archived release:** https://doi.org/10.5281/zenodo.23496185

**Version-specific source:** https://github.com/Adit-Mugdha-das/NeuroBloom/tree/v1.2.2

GitHub also provides a **Cite this repository** option using the included `CITATION.cff` file.

## Contact

For questions, contact:

```text
aditmugdhadas@gmail.com
```
