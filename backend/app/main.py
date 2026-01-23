from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.auth import router as auth_router
from app.api.tasks import router as tasks_router
from app.api.baseline import router as baseline_router
from app.api.training import router as training_router
from app.api.doctor import router as doctor_router
from app.core.config import init_db

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

app.include_router(auth_router, prefix="/api/auth")
app.include_router(tasks_router, prefix="/api/tasks")
app.include_router(baseline_router, prefix="/api/baseline")
app.include_router(training_router, prefix="/api/training")
app.include_router(doctor_router, prefix="/api")  # Doctor routes include /doctor prefix already

@app.get("/")
def root():
    return {"message": "MS-Cognitive Training Backend Running"}

@app.get("/favicon.ico")
def favicon():
    return {"message": "No favicon"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
