# NeuroBloom

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23106598.svg)](https://doi.org/10.5281/zenodo.23106598)

NeuroBloom is a free-of-cost, modular web platform for longitudinal cognitive monitoring and clinician-guided rehabilitation in multiple sclerosis (MS). It is designed for patients, clinicians, and administrators who need structured cognitive follow-up between formal clinical encounters, particularly in settings where repeated specialist assessment may be difficult to access. The project is associated with a SoftwareX journal publication and provides a reproducible software framework for digital rehabilitation research and pilot deployment. A deployed version is available at https://neurobloom-67qo.onrender.com/.

## Key Features

- 35 cognitive tasks across 6 cognitive domains, each with 10 difficulty levels
- Pre-session contextual capture for fatigue, sleep quality, stress, and medication timing
- Descriptive longitudinal indicators supporting future digital-biomarker-oriented research
- Three-role architecture for patients, clinicians, and administrators
- Bilingual support in Bengali and English
- Configurable review flags for clinician interpretation and bidirectional messaging
- Free-of-cost and open source under the MIT License

## System Requirements

- Python 3.10+
- Node.js 18+
- npm
- PostgreSQL 14+
- Modern web browser

## Installation

1. Clone the repository.

```bash
git clone https://github.com/Adit-Mugdha-das/NeuroBloom.git
cd NeuroBloom
```

2. Set up the backend.

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

3. Copy the environment template and configure database settings.

```bash
cd ..

# Windows PowerShell
Copy-Item .env.example .env.local

# macOS / Linux
cp .env.example .env.local
```

Edit `.env.local` with your local PostgreSQL database name, username, password, host, port, and allowed frontend origins. For local development without Docker, ensure PostgreSQL is running and the configured database exists before starting the backend. Leave `DATABASE_URL` commented unless you intentionally want to override the individual PostgreSQL settings.

If the configured database does not exist yet, create it before initialization:

```bash
createdb neurobloom_db
```

Alternatively, using `psql`:

```bash
psql -U postgres -c "CREATE DATABASE neurobloom_db;"
```

4. Initialize the database.

```bash
cd backend
python seed_initial_data.py
```

5. Start the backend API.

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

6. Set up and start the frontend.

```bash
cd ../frontend-svelte
npm install
npm run dev
```

The frontend development server runs on `http://localhost:5174`, and the backend API runs on `http://127.0.0.1:8000`.

## Running with Docker

Docker Compose is the recommended setup for local deployment. It starts PostgreSQL, the backend API, and the frontend container.

```bash
# Windows PowerShell
Copy-Item .env.example .env.local

# macOS / Linux
cp .env.example .env.local

docker compose --env-file .env.local -f compose.yaml up --build
```

After the containers are running, initialize the default admin account and reference data once:

```bash
docker compose --env-file .env.local -f compose.yaml exec backend python seed_initial_data.py
```

The frontend is available at `http://localhost:8080`, and the backend API is available at `http://localhost:8000`.

If your Docker installation uses the older standalone Compose binary, replace `docker compose` with `docker-compose`.

## Reproducing the manuscript demonstration

This procedure deploys NeuroBloom with Docker Compose, generates synthetic demonstration data, and regenerates the sensitivity results reported in the supplementary material. Only Docker with Compose is required on the host; the containers use Python 3.12, Node.js 20, and PostgreSQL 16. Run all commands from the repository root.

1. Create the environment file and start the system.

```bash
# Windows PowerShell
Copy-Item .env.example .env.local

# macOS / Linux
cp .env.example .env.local

docker compose --env-file .env.local -f compose.yaml up --build -d
```

2. Initialize the database and the cognitive-task library (once).

```bash
docker compose --env-file .env.local -f compose.yaml exec backend python seed_initial_data.py
```

3. Generate the synthetic demonstration data.

```bash
docker compose --env-file .env.local -f compose.yaml exec backend python scripts/seed_demo_clinical_data.py
```

The script creates 8 synthetic clinicians and 8 synthetic patients, each patient assigned to one clinician, with baseline assessments, training plans, 60 training sessions with contextual records, progress reports, prescriptions, messages, and review flags. It prints every account it creates. Running it again replaces the previous demonstration records. The script uses a fixed random seed to reproduce the same synthetic patient profiles and performance values; record dates are generated relative to the execution date.

4. Open the application at `http://localhost:8080` and sign in with the demonstration accounts, for example:

| Role | Email | Password |
|------|-------|----------|
| Clinician | `dr.samira.rahman@demo.neurobloom.example` | `doctor1234` |
| Patient | `sharmin.akter@demo.neurobloom.example` | `patient1234` |

The clinician account shows the assigned patient's baseline, session history, trends, and longitudinal analytics; the patient account shows the patient workflow.

5. Regenerate the sensitivity results.

```bash
docker compose --env-file .env.local -f compose.yaml exec backend python scripts/fatigue_proxy_sensitivity.py
docker compose --env-file .env.local -f compose.yaml exec backend python scripts/trend_sensitivity.py
docker compose --env-file .env.local -f compose.yaml exec backend python scripts/illustrative_case.py
docker compose --env-file .env.local -f compose.yaml cp backend:/app/analysis/results/. backend/analysis/results
```

Each script prints its results and writes a JSON file to `analysis/results/` (`/app/analysis/results/` in the container); the last command copies the files to `backend/analysis/results/`. `illustrative_case.py` produces the synthetic longitudinal case shown in the manuscript. Without Docker, run the same scripts with `python scripts/<name>.py` from the `backend` directory, which writes to the same location.

The demonstration accounts above, and the default administrator account created by `seed_initial_data.py`, use fixed passwords and are intended for local demonstration only. Do not use them in a real deployment; change or remove them first.

## API Documentation

NeuroBloom exposes an automatically generated OpenAPI (Swagger UI) interface through FastAPI for exploring and testing backend REST API endpoints.

After starting the backend, the API documentation is available at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

These interfaces provide interactive documentation for all available API endpoints, request parameters, and response schemas.

## Project Structure

```text
NeuroBloom/
|-- backend/                 # FastAPI backend, SQLModel models, APIs, services, seed scripts
|-- frontend-svelte/         # SvelteKit frontend application
|-- Paper_Materials/         # SoftwareX manuscript, figures, and publication materials
|-- demo/                    # Supplementary demo video
|-- compose.yaml             # Docker Compose configuration
|-- .env.example             # Environment variable template
|-- LICENSE                  # MIT License
`-- README.md                # Project documentation
```

## User Roles

Patients complete baseline and training activities, submit contextual information, review progress, receive prescriptions, and communicate with clinicians.

Clinicians review patient histories, monitor longitudinal trends and review flags, adjust rehabilitation plans, issue prescriptions, generate reports, and exchange messages with assigned patients.

Administrators manage users, departments, assignments, notifications, audit logs, system health, and research-oriented data export.

## Supplementary Video

A supplementary screencast demonstrating the main NeuroBloom workflows is available at:

```text
demo/NeuroBloom_demo.mp4
```

## Tech Stack

- Python
- FastAPI
- SQLModel
- PostgreSQL
- JavaScript
- Svelte
- SvelteKit
- Vite

## License

NeuroBloom is released under the MIT License. See [LICENSE](LICENSE) for details.


## Citation

If you use NeuroBloom in your research, please cite the archived software release.

> Das, A. M., Deb Nath, A., Alam, K. S., & Hossain, S. I. (2026). *Adit-Mugdha-das/NeuroBloom: NeuroBloom v1.2 – SoftwareX Archive Release* (Version v1.2) [Computer software]. Zenodo. [https://doi.org/10.5281/zenodo.23106598](https://doi.org/10.5281/zenodo.23106598)

GitHub also provides a **"Cite this repository"** option through the included `CITATION.cff` file.

## Contact

For questions, contact:

```text
aditmugdhadas@gmail.com
```
