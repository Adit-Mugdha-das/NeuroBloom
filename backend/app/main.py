from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.auth import router as auth_router
from app.api.tasks import router as tasks_router
from app.api.baseline import router as baseline_router
from app.core.config import init_db

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

app.include_router(auth_router, prefix="/auth")
app.include_router(tasks_router, prefix="/tasks")
app.include_router(baseline_router, prefix="/baseline")

@app.get("/")
def root():
    return {"message": "MS-Cognitive Training Backend Running"}

@app.get("/favicon.ico")
def favicon():
    return {"message": "No favicon"}
