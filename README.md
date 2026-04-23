# NeuroBloom

NeuroBloom is a cognitive training and monitoring platform with a FastAPI backend, a SvelteKit frontend, and PostgreSQL for persistence.

## Stack

- Backend: FastAPI, SQLModel, PostgreSQL
- Frontend: SvelteKit, Vite, Axios
- Deployment: Docker Compose, Nginx, Postgres

## Docker Setup

1. Copy `.env.example` to `.env.local`.
2. Fill in your local Postgres credentials and allowed origins.
3. Run:

```bash
docker compose up --build
```

The app will be available at `http://localhost:8080`.

## Local Development

1. Create `.env.local` from `.env.example`.
2. Start PostgreSQL locally with the same credentials.
3. Run the backend:

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

4. Run the frontend:

```bash
cd frontend-svelte
npm install
npm run dev
```

The frontend runs on `http://localhost:5174` and proxies `/api` to the backend.

## Configuration

- Shared local config lives in `.env.local` at the repo root.
- Docker Compose and backend settings both read from that file.
- `DATABASE_URL` is optional; if omitted, the backend derives it from `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD`.

## Notes

- The frontend now uses same-origin `/api` requests in production.
- The Docker deployment exposes only the frontend on port `8080`; backend and Postgres stay on the internal Compose network.
