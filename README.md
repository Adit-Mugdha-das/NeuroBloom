
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

The demonstration was tested using:

| Component | Tested environment |
|---|---|
| Host operating system | Windows 10 Pro, build 19045 |
| Docker | Docker Desktop, Docker 29.2.0 |
| Docker Compose | v5.0.2 |
| Backend container | Python 3.12 |
| Frontend container | Node.js 20 |
| Database container | PostgreSQL 16 |
| Browser | Google Chrome 151.0.7922.138 |
| Browser | Microsoft Edge 154.0.4258.37 |

Other operating systems and supported dependency versions may work but are not covered by this specific reproduction record.

## Software Testing and Continuous Integration

NeuroBloom includes automated backend and frontend tests to check software functionality and the consistency of its recorded outputs.

### Test Coverage

The backend suite contains **118 pytest tests**, covering numerical scoring, trial generation, response classification, difficulty adjustment, task inventory, analytics, API endpoints, and patient–clinician interactions.

The frontend suite contains **26 Vitest tests**, covering scoring functions, task navigation, the baseline workflow, progress summaries, and analytics display behaviour.

An API-level integration test covers patient registration, clinician assignment, baseline completion, training-plan generation, completion of a four-task session, difficulty adaptation, and clinician access to patient records. It also verifies that a clinician without an approved assignment cannot retrieve another patient's records.

At the time of the reported revision verification:

| Metric | Result |
|---|---|
| Backend tests | 118 |
| Frontend tests | 26 |
| Total tests | 144 |
| Test status | All 144 passed |
| Backend line coverage | Approximately 40% |
| Frontend line coverage | Approximately 13% |

These coverage figures describe the reported revision run, not a new measurement from every subsequent commit.

### Running Backend Tests

From the repository root:

```bash
cd backend

pip install -r requirements.txt
pip install pytest pytest-httpx pytest-cov

pytest tests/ -v --tb=short --cov=app --cov-report=term
```

The backend tests use an isolated in-memory SQLite database instead of PostgreSQL, so a running PostgreSQL server is not required for the test suite.

### Running Frontend Tests

From the repository root:

```bash
cd frontend-svelte

npm ci
npm run test:coverage
```

The command executes the Vitest suite and produces a coverage summary.

### GitHub Actions

Continuous integration is configured in:

`.github/workflows/tests.yml`

GitHub Actions runs the automated suites for pushes and pull requests targeting the `main` or `master` branches.

The CI environment uses:

- Ubuntu runners
- Python 3.12 for backend tests
- Node.js 20 for frontend tests
- pytest and Vitest for testing
- Coverage reporting for both suites

The automated tests check implementation behaviour but do not establish the psychometric or clinical validity of NeuroBloom's cognitive tasks.

### Testing Limitations

The current test suite has several limitations:

- Backend API tests use SQLite rather than production PostgreSQL.
- Frontend tests focus on scoring and workflow logic rather than Svelte page components.
- Browser-level end-to-end tests are not yet included.
- Coverage is incomplete, particularly for API, page, and user-interface code.

Further testing will be needed before the software can be considered for sensitive multi-user or clinical deployment.

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

NeuroBloom is a research software prototype intended for isolated demonstrations using synthetic data.

Passwords are protected using bcrypt hashing and checked at login. However, subsequent API requests are not bound to server-verified authenticated sessions. Some endpoints rely on caller-supplied account identifiers, and consent revocation is not consistently enforced across all relevant endpoints.

These limitations mean the current software should not be used with real patient data or sensitive multi-user records. Stronger authentication, consistent authorization, security testing, and appropriate data protection measures are required before such deployment.

The demonstration accounts and default administrator account use fixed passwords for local testing. They must not be used in production.

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
