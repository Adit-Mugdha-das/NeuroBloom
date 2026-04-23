# NeuroBloom Frontend

SvelteKit frontend for NeuroBloom.

## Development

Prerequisites:

- Node.js 18+
- Backend running locally on port `8000`

Install and run:

```bash
cd frontend-svelte
npm install
npm run dev
```

The dev server runs on `http://localhost:5174` and proxies `/api` to the backend target from `VITE_API_PROXY_TARGET` or `http://127.0.0.1:8000` by default.

## Production Build

```bash
npm run build
```

The app is built as a static SPA with an `index.html` fallback for deep links.

## Docker

The production container build is defined in:

- `frontend-svelte/Dockerfile`
- `frontend-svelte/nginx.conf`

In Docker, Nginx serves the built frontend and proxies `/api` to the backend service.
