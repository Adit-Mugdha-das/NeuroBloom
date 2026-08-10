# NeuroBloom

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21207720.svg)](https://doi.org/10.5281/zenodo.21207720)

NeuroBloom is a free-of-cost, modular web platform for longitudinal cognitive monitoring and clinician-guided rehabilitation in multiple sclerosis (MS). It is designed for patients, clinicians, and administrators who need structured cognitive follow-up between formal clinical encounters, particularly in settings where repeated specialist assessment may be difficult to access. The project is associated with a SoftwareX journal publication and provides a reproducible software framework for digital rehabilitation research and pilot deployment. A deployed version is available at https://neurobloom-67qo.onrender.com/.

## Key Features

- 35 cognitive tasks across 6 cognitive domains, each with 10 difficulty levels
- Pre-session contextual capture for fatigue, sleep quality, stress, and medication timing
- Longitudinal analytics with digital biomarker extraction
- Three-role architecture for patients, clinicians, and administrators
- Bilingual support in Bengali and English
- Automated high-risk patient alerts and bidirectional messaging
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

Clinicians review patient histories, monitor longitudinal trends and risk alerts, adjust rehabilitation plans, issue prescriptions, generate reports, and exchange messages with assigned patients.

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

> Das, A. M., Deb Nath, A., Alam, K. S., & Hossain, S. I. (2026). *Adit-Mugdha-das/NeuroBloom: NeuroBloom v1.1 – SoftwareX Archive Release* (Version v1.1) [Computer software]. Zenodo. [https://doi.org/10.5281/zenodo.21207720](https://doi.org/10.5281/zenodo.21207720)

GitHub also provides a **"Cite this repository"** option through the included `CITATION.cff` file.

## Contact

For questions, contact:

```text
aditmugdhadas@gmail.com
```
