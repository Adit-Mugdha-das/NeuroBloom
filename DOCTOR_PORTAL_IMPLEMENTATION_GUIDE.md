# 🏥 Doctor Portal Implementation Guide
**NeuroBloom - Clinician Dashboard Feature**

---

## 📋 Overview

Add a comprehensive doctor/clinician portal that enables healthcare providers to:
- ✅ Login as a doctor (separate from patient login)
- ✅ View list of assigned patients
- ✅ Monitor each patient's cognitive performance
- ✅ Review detailed analytics and trends
- ✅ Adjust training plans and provide recommendations
- ✅ Generate clinical reports
- ✅ Track intervention effectiveness

---

## 🗂️ STEP 1: Database Models

### 1.1 Create Doctor Model
**File**: `backend/app/models/doctor.py`

```python
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime

class Doctor(SQLModel, table=True):
    """Healthcare provider/clinician model"""
    __tablename__ = "doctors"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    password_hash: str
    
    # Professional info
    full_name: str
    license_number: Optional[str] = Field(default=None)
    specialization: Optional[str] = Field(default=None)  # "Neurologist", "Neuropsychologist", etc.
    institution: Optional[str] = Field(default=None)
    
    # Account management
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)  # Require admin verification
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = Field(default=None)
    
    # Relationships
    patient_assignments: List["PatientAssignment"] = Relationship(back_populates="doctor")
```

### 1.2 Create Patient Assignment Model
**File**: `backend/app/models/patient_assignment.py`

```python
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime

class PatientAssignment(SQLModel, table=True):
    """Links doctors to their patients"""
    __tablename__ = "patient_assignments"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    doctor_id: int = Field(foreign_key="doctors.id", index=True)
    patient_id: int = Field(foreign_key="user.id", index=True)  # References User table
    
    # Assignment details
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    assigned_by: Optional[int] = Field(default=None)  # Admin who made assignment
    is_active: bool = Field(default=True)
    
    # Clinical context
    diagnosis: Optional[str] = Field(default=None)  # "RRMS", "PPMS", etc.
    notes: Optional[str] = Field(default=None)
    treatment_goal: Optional[str] = Field(default=None)
    
    # Relationships
    doctor: Optional["Doctor"] = Relationship(back_populates="patient_assignments")
```

### 1.3 Update User Model
**File**: `backend/app/models/user.py`

```python
from sqlmodel import SQLModel, Field
from typing import Optional

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str
    password_hash: str
    
    # NEW: Add patient-specific fields
    full_name: Optional[str] = Field(default=None)
    date_of_birth: Optional[str] = Field(default=None)
    diagnosis: Optional[str] = Field(default=None)
    consent_to_share: bool = Field(default=False)  # Patient consent for doctor access
```

### 1.4 Create Doctor Intervention Model (Optional but Recommended)
**File**: `backend/app/models/doctor_intervention.py`

```python
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class DoctorIntervention(SQLModel, table=True):
    """Track doctor actions and recommendations"""
    __tablename__ = "doctor_interventions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    doctor_id: int = Field(foreign_key="doctors.id")
    patient_id: int = Field(foreign_key="user.id")
    
    intervention_type: str  # "training_plan_adjustment", "note", "recommendation"
    description: str
    intervention_data: Optional[str] = Field(default=None)  # JSON for structured data
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### 1.5 Update Models __init__.py
**File**: `backend/app/models/__init__.py`

```python
from app.models.user import User
from app.models.doctor import Doctor
from app.models.patient_assignment import PatientAssignment
from app.models.doctor_intervention import DoctorIntervention
# ... other imports
```

---

## 🔐 STEP 2: Authentication System

### 2.1 Create Doctor Schemas
**File**: `backend/app/schemas/doctor.py`

```python
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class DoctorCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    license_number: Optional[str] = None
    specialization: Optional[str] = None
    institution: Optional[str] = None

class DoctorLogin(BaseModel):
    email: EmailStr
    password: str

class DoctorRead(BaseModel):
    id: int
    email: str
    full_name: str
    specialization: Optional[str]
    institution: Optional[str]
    is_verified: bool
    
    class Config:
        from_attributes = True

class PatientAssignmentCreate(BaseModel):
    patient_email: str  # Will lookup patient by email
    diagnosis: Optional[str] = None
    notes: Optional[str] = None
    treatment_goal: Optional[str] = None
```

### 2.2 Update Authentication API
**File**: `backend/app/api/auth.py`

```python
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from app.models.user import User
from app.models.doctor import Doctor
from app.schemas.user import UserCreate, UserLogin, UserRead
from app.schemas.doctor import DoctorCreate, DoctorLogin, DoctorRead
from app.core.config import engine
from app.core.security import hash_password, verify_password
import traceback

router = APIRouter()

def get_session():
    with Session(engine) as session:
        yield session

# ========== PATIENT ENDPOINTS (Existing) ==========
@router.post("/register", response_model=UserRead)
def register_patient(user: UserCreate, session: Session = Depends(get_session)):
    try:
        existing = session.exec(select(User).where(User.email == user.email)).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        user_db = User(email=user.email, password_hash=hash_password(user.password))
        session.add(user_db)
        session.commit()
        session.refresh(user_db)
        return user_db
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login")
def login_patient(user: UserLogin, session: Session = Depends(get_session)):
    try:
        user_db = session.exec(select(User).where(User.email == user.email)).first()
        
        if not user_db:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        if not verify_password(user.password, user_db.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        return {
            "message": "Login successful",
            "email": user_db.email,
            "id": user_db.id,
            "role": "patient"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ========== DOCTOR ENDPOINTS (NEW) ==========
@router.post("/doctor/register", response_model=DoctorRead)
def register_doctor(doctor: DoctorCreate, session: Session = Depends(get_session)):
    """Register new doctor (requires admin approval)"""
    try:
        # Check if email already exists
        existing = session.exec(select(Doctor).where(Doctor.email == doctor.email)).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Also check in patient table
        existing_patient = session.exec(select(User).where(User.email == doctor.email)).first()
        if existing_patient:
            raise HTTPException(status_code=400, detail="Email already registered as patient")

        doctor_db = Doctor(
            email=doctor.email,
            password_hash=hash_password(doctor.password),
            full_name=doctor.full_name,
            license_number=doctor.license_number,
            specialization=doctor.specialization,
            institution=doctor.institution,
            is_verified=False  # Requires admin approval
        )
        session.add(doctor_db)
        session.commit()
        session.refresh(doctor_db)
        return doctor_db
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/doctor/login")
def login_doctor(doctor: DoctorLogin, session: Session = Depends(get_session)):
    """Doctor login endpoint"""
    try:
        doctor_db = session.exec(select(Doctor).where(Doctor.email == doctor.email)).first()
        
        if not doctor_db:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        if not doctor_db.is_active:
            raise HTTPException(status_code=403, detail="Account deactivated")
        
        if not doctor_db.is_verified:
            raise HTTPException(status_code=403, detail="Account pending verification")
        
        if not verify_password(doctor.password, doctor_db.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Update last login
        doctor_db.last_login = datetime.utcnow()
        session.add(doctor_db)
        session.commit()
        
        return {
            "message": "Login successful",
            "email": doctor_db.email,
            "id": doctor_db.id,
            "role": "doctor",
            "full_name": doctor_db.full_name,
            "is_verified": doctor_db.is_verified
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 🏥 STEP 3: Doctor API Endpoints

### 3.1 Create Doctor API Router
**File**: `backend/app/api/doctor.py`

```python
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from typing import List
from datetime import datetime, timedelta
from app.models.doctor import Doctor
from app.models.user import User
from app.models.patient_assignment import PatientAssignment
from app.models.training_session import TrainingSession
from app.models.training_plan import TrainingPlan
from app.models.baseline_assessment import BaselineAssessment
from app.core.config import engine
import statistics

router = APIRouter(prefix="/doctor", tags=["doctor"])

def get_session():
    with Session(engine) as session:
        yield session

# ========== PATIENT MANAGEMENT ==========
@router.get("/{doctor_id}/patients")
def get_doctor_patients(doctor_id: int, session: Session = Depends(get_session)):
    """Get list of all patients assigned to this doctor"""
    try:
        # Verify doctor exists
        doctor = session.get(Doctor, doctor_id)
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")
        
        # Get all active patient assignments
        assignments = session.exec(
            select(PatientAssignment)
            .where(PatientAssignment.doctor_id == doctor_id)
            .where(PatientAssignment.is_active == True)
        ).all()
        
        patients_data = []
        for assignment in assignments:
            patient = session.get(User, assignment.patient_id)
            if not patient:
                continue
            
            # Get latest training session
            latest_session = session.exec(
                select(TrainingSession)
                .where(TrainingSession.user_id == patient.id)
                .order_by(TrainingSession.completed_at.desc())
            ).first()
            
            # Get baseline assessment
            baseline = session.exec(
                select(BaselineAssessment)
                .where(BaselineAssessment.user_id == patient.id)
            ).first()
            
            patients_data.append({
                "patient_id": patient.id,
                "email": patient.email,
                "full_name": patient.full_name,
                "diagnosis": assignment.diagnosis,
                "assigned_at": assignment.assigned_at,
                "last_activity": latest_session.completed_at if latest_session else None,
                "baseline_completed": baseline is not None,
                "treatment_goal": assignment.treatment_goal
            })
        
        return {"patients": patients_data, "total": len(patients_data)}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{doctor_id}/assign-patient")
def assign_patient(
    doctor_id: int,
    patient_email: str,
    diagnosis: str = None,
    notes: str = None,
    treatment_goal: str = None,
    session: Session = Depends(get_session)
):
    """Assign a patient to this doctor"""
    try:
        # Verify doctor exists
        doctor = session.get(Doctor, doctor_id)
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")
        
        # Find patient by email
        patient = session.exec(select(User).where(User.email == patient_email)).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Check if patient has given consent (optional, but good practice)
        if not patient.consent_to_share:
            raise HTTPException(
                status_code=403,
                detail="Patient has not consented to data sharing with healthcare providers"
            )
        
        # Check if already assigned
        existing = session.exec(
            select(PatientAssignment)
            .where(PatientAssignment.doctor_id == doctor_id)
            .where(PatientAssignment.patient_id == patient.id)
            .where(PatientAssignment.is_active == True)
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Patient already assigned to this doctor")
        
        # Create assignment
        assignment = PatientAssignment(
            doctor_id=doctor_id,
            patient_id=patient.id,
            diagnosis=diagnosis,
            notes=notes,
            treatment_goal=treatment_goal
        )
        session.add(assignment)
        session.commit()
        session.refresh(assignment)
        
        return {
            "message": "Patient assigned successfully",
            "assignment_id": assignment.id,
            "patient_email": patient.email
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ========== PATIENT ANALYTICS ==========
@router.get("/{doctor_id}/patient/{patient_id}/overview")
def get_patient_overview(
    doctor_id: int,
    patient_id: int,
    session: Session = Depends(get_session)
):
    """Get comprehensive overview of a patient's progress"""
    try:
        # Verify doctor has access to this patient
        assignment = session.exec(
            select(PatientAssignment)
            .where(PatientAssignment.doctor_id == doctor_id)
            .where(PatientAssignment.patient_id == patient_id)
            .where(PatientAssignment.is_active == True)
        ).first()
        
        if not assignment:
            raise HTTPException(status_code=403, detail="No access to this patient")
        
        # Get patient info
        patient = session.get(User, patient_id)
        
        # Get baseline assessment
        baseline = session.exec(
            select(BaselineAssessment)
            .where(BaselineAssessment.user_id == patient_id)
        ).first()
        
        # Get training plan
        training_plan = session.exec(
            select(TrainingPlan)
            .where(TrainingPlan.user_id == patient_id)
        ).first()
        
        # Get all training sessions
        all_sessions = session.exec(
            select(TrainingSession)
            .where(TrainingSession.user_id == patient_id)
            .order_by(TrainingSession.completed_at.desc())
        ).all()
        
        # Calculate statistics
        total_sessions = len(all_sessions)
        
        # Recent performance (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_sessions = [s for s in all_sessions if s.completed_at >= seven_days_ago]
        
        avg_recent_score = statistics.mean([s.score for s in recent_sessions]) if recent_sessions else 0
        avg_recent_accuracy = statistics.mean([s.accuracy for s in recent_sessions]) if recent_sessions else 0
        
        # Domain-specific performance
        domain_stats = {}
        for domain in ["working_memory", "attention", "flexibility", "planning", "processing_speed", "visual_scanning"]:
            domain_sessions = [s for s in all_sessions if s.domain == domain]
            if domain_sessions:
                domain_stats[domain] = {
                    "count": len(domain_sessions),
                    "avg_score": statistics.mean([s.score for s in domain_sessions]),
                    "avg_accuracy": statistics.mean([s.accuracy for s in domain_sessions]),
                    "baseline_score": getattr(baseline, f"{domain}_score", None) if baseline else None
                }
        
        return {
            "patient_info": {
                "id": patient.id,
                "email": patient.email,
                "full_name": patient.full_name,
                "diagnosis": assignment.diagnosis,
                "treatment_goal": assignment.treatment_goal
            },
            "baseline": {
                "completed": baseline is not None,
                "date": baseline.assessment_date if baseline else None,
                "overall_score": baseline.overall_cognitive_score if baseline else None,
                "domain_scores": {
                    "working_memory": baseline.working_memory_score if baseline else None,
                    "attention": baseline.attention_score if baseline else None,
                    "flexibility": baseline.flexibility_score if baseline else None,
                    "planning": baseline.planning_score if baseline else None,
                    "processing_speed": baseline.processing_speed_score if baseline else None,
                    "visual_scanning": baseline.visual_scanning_score if baseline else None
                } if baseline else None
            },
            "training_summary": {
                "total_sessions": total_sessions,
                "current_streak": training_plan.current_streak if training_plan else 0,
                "longest_streak": training_plan.longest_streak if training_plan else 0,
                "last_session": all_sessions[0].completed_at if all_sessions else None
            },
            "recent_performance": {
                "sessions_last_7_days": len(recent_sessions),
                "avg_score": round(avg_recent_score, 1),
                "avg_accuracy": round(avg_recent_accuracy, 1)
            },
            "domain_performance": domain_stats,
            "focus_areas": {
                "primary": training_plan.primary_focus if training_plan else [],
                "secondary": training_plan.secondary_focus if training_plan else [],
                "maintenance": training_plan.maintenance if training_plan else []
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{doctor_id}/patient/{patient_id}/sessions")
def get_patient_sessions(
    doctor_id: int,
    patient_id: int,
    limit: int = 50,
    session: Session = Depends(get_session)
):
    """Get detailed session history for a patient"""
    try:
        # Verify access
        assignment = session.exec(
            select(PatientAssignment)
            .where(PatientAssignment.doctor_id == doctor_id)
            .where(PatientAssignment.patient_id == patient_id)
            .where(PatientAssignment.is_active == True)
        ).first()
        
        if not assignment:
            raise HTTPException(status_code=403, detail="No access to this patient")
        
        # Get sessions
        sessions = session.exec(
            select(TrainingSession)
            .where(TrainingSession.user_id == patient_id)
            .order_by(TrainingSession.completed_at.desc())
            .limit(limit)
        ).all()
        
        sessions_data = [{
            "id": s.id,
            "domain": s.domain,
            "task_type": s.task_type,
            "task_code": s.task_code,
            "difficulty": s.difficulty_level,
            "score": s.score,
            "accuracy": s.accuracy,
            "reaction_time": s.reaction_time,
            "completed_at": s.completed_at,
            "duration_seconds": s.duration_seconds
        } for s in sessions]
        
        return {"sessions": sessions_data, "total": len(sessions_data)}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ========== CLINICAL RECOMMENDATIONS ==========
@router.post("/{doctor_id}/patient/{patient_id}/intervention")
def add_intervention(
    doctor_id: int,
    patient_id: int,
    intervention_type: str,
    description: str,
    session: Session = Depends(get_session)
):
    """Add a clinical note or intervention for a patient"""
    try:
        # Verify access
        assignment = session.exec(
            select(PatientAssignment)
            .where(PatientAssignment.doctor_id == doctor_id)
            .where(PatientAssignment.patient_id == patient_id)
            .where(PatientAssignment.is_active == True)
        ).first()
        
        if not assignment:
            raise HTTPException(status_code=403, detail="No access to this patient")
        
        from app.models.doctor_intervention import DoctorIntervention
        
        intervention = DoctorIntervention(
            doctor_id=doctor_id,
            patient_id=patient_id,
            intervention_type=intervention_type,
            description=description
        )
        session.add(intervention)
        session.commit()
        
        return {"message": "Intervention recorded successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 3.2 Register Doctor Router in Main
**File**: `backend/app/main.py`

```python
from fastapi import FastAPI
from app.api import auth, tasks, training, baseline, doctor  # Add doctor
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(training.router, prefix="/training", tags=["training"])
app.include_router(baseline.router, prefix="/baseline", tags=["baseline"])
app.include_router(doctor.router, prefix="/api", tags=["doctor"])  # NEW

@app.get("/")
def root():
    return {"message": "NeuroBloom API"}
```

---

## 🎨 STEP 4: Frontend Implementation

### 4.1 Update Login Page to Support Doctor Login
**File**: `frontend-svelte/src/routes/auth/login/+page.svelte`

```svelte
<script>
    import { goto } from '$app/navigation';
    import api from '$lib/api.js';
    import { user } from '$lib/stores.js';
    
    let email = '';
    let password = '';
    let loginType = 'patient'; // 'patient' or 'doctor'
    let error = '';
    let loading = false;
    
    async function handleLogin() {
        if (!email || !password) {
            error = 'Please fill in all fields';
            return;
        }
        
        loading = true;
        error = '';
        
        try {
            const endpoint = loginType === 'doctor' 
                ? '/auth/doctor/login' 
                : '/auth/login';
            
            const response = await api.post(endpoint, { email, password });
            
            // Store user data
            user.set({
                id: response.data.id,
                email: response.data.email,
                role: response.data.role || loginType,
                fullName: response.data.full_name || null
            });
            
            // Redirect based on role
            if (loginType === 'doctor') {
                goto('/doctor/dashboard');
            } else {
                goto('/dashboard');
            }
        } catch (err) {
            error = err.response?.data?.detail || 'Login failed';
        } finally {
            loading = false;
        }
    }
</script>

<div class="login-container">
    <div class="login-card">
        <h1>Login to NeuroBloom</h1>
        
        <!-- Login Type Selector -->
        <div class="login-type-selector">
            <button 
                class="type-btn {loginType === 'patient' ? 'active' : ''}"
                on:click={() => loginType = 'patient'}
            >
                Patient
            </button>
            <button 
                class="type-btn {loginType === 'doctor' ? 'active' : ''}"
                on:click={() => loginType = 'doctor'}
            >
                Doctor
            </button>
        </div>
        
        <form on:submit|preventDefault={handleLogin}>
            <div class="form-group">
                <label for="email">Email</label>
                <input 
                    type="email" 
                    id="email" 
                    bind:value={email} 
                    placeholder="Enter your email"
                    required
                />
            </div>
            
            <div class="form-group">
                <label for="password">Password</label>
                <input 
                    type="password" 
                    id="password" 
                    bind:value={password} 
                    placeholder="Enter your password"
                    required
                />
            </div>
            
            {#if error}
                <div class="error">{error}</div>
            {/if}
            
            <button type="submit" class="login-btn" disabled={loading}>
                {loading ? 'Logging in...' : `Login as ${loginType === 'doctor' ? 'Doctor' : 'Patient'}`}
            </button>
        </form>
        
        <p class="register-link">
            Don't have an account? 
            <a href="/auth/register">Register here</a>
        </p>
    </div>
</div>

<style>
    .login-container {
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .login-card {
        background: white;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        width: 100%;
        max-width: 400px;
    }
    
    h1 {
        text-align: center;
        margin-bottom: 1.5rem;
        color: #333;
    }
    
    .login-type-selector {
        display: flex;
        gap: 0.5rem;
        margin-bottom: 1.5rem;
        background: #f0f0f0;
        border-radius: 8px;
        padding: 4px;
    }
    
    .type-btn {
        flex: 1;
        padding: 0.75rem;
        border: none;
        background: transparent;
        border-radius: 6px;
        cursor: pointer;
        font-weight: 500;
        transition: all 0.3s;
    }
    
    .type-btn.active {
        background: white;
        color: #667eea;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .form-group {
        margin-bottom: 1rem;
    }
    
    label {
        display: block;
        margin-bottom: 0.5rem;
        font-weight: 500;
        color: #555;
    }
    
    input {
        width: 100%;
        padding: 0.75rem;
        border: 2px solid #e0e0e0;
        border-radius: 6px;
        font-size: 1rem;
        transition: border-color 0.3s;
    }
    
    input:focus {
        outline: none;
        border-color: #667eea;
    }
    
    .error {
        background: #fee;
        color: #c33;
        padding: 0.75rem;
        border-radius: 6px;
        margin-bottom: 1rem;
        text-align: center;
    }
    
    .login-btn {
        width: 100%;
        padding: 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 6px;
        font-size: 1rem;
        font-weight: 600;
        cursor: pointer;
        transition: transform 0.2s;
    }
    
    .login-btn:hover:not(:disabled) {
        transform: translateY(-2px);
    }
    
    .login-btn:disabled {
        opacity: 0.6;
        cursor: not-allowed;
    }
    
    .register-link {
        text-align: center;
        margin-top: 1rem;
        color: #666;
    }
    
    .register-link a {
        color: #667eea;
        text-decoration: none;
        font-weight: 600;
    }
</style>
```

### 4.2 Create Doctor Dashboard
**File**: `frontend-svelte/src/routes/doctor/dashboard/+page.svelte`

```svelte
<script>
    import { onMount } from 'svelte';
    import { user } from '$lib/stores.js';
    import { goto } from '$app/navigation';
    import api from '$lib/api.js';
    
    let patients = [];
    let loading = true;
    let error = '';
    
    onMount(async () => {
        // Check if user is logged in as doctor
        if (!$user || $user.role !== 'doctor') {
            goto('/auth/login');
            return;
        }
        
        await loadPatients();
    });
    
    async function loadPatients() {
        try {
            const response = await api.get(`/api/doctor/${$user.id}/patients`);
            patients = response.data.patients;
        } catch (err) {
            error = 'Failed to load patients';
            console.error(err);
        } finally {
            loading = false;
        }
    }
    
    function viewPatient(patientId) {
        goto(`/doctor/patient/${patientId}`);
    }
    
    function formatDate(dateStr) {
        if (!dateStr) return 'Never';
        return new Date(dateStr).toLocaleDateString();
    }
</script>

<div class="doctor-dashboard">
    <header>
        <h1>👨‍⚕️ Doctor Dashboard</h1>
        <p>Welcome, Dr. {$user?.fullName || $user?.email}</p>
    </header>
    
    {#if loading}
        <div class="loading">Loading patients...</div>
    {:else if error}
        <div class="error">{error}</div>
    {:else}
        <div class="stats-cards">
            <div class="stat-card">
                <div class="stat-number">{patients.length}</div>
                <div class="stat-label">Total Patients</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">
                    {patients.filter(p => p.last_activity && 
                        new Date(p.last_activity) > new Date(Date.now() - 7*24*60*60*1000)).length}
                </div>
                <div class="stat-label">Active (7 days)</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">
                    {patients.filter(p => p.baseline_completed).length}
                </div>
                <div class="stat-label">Baseline Complete</div>
            </div>
        </div>
        
        <div class="patients-section">
            <h2>Your Patients</h2>
            
            {#if patients.length === 0}
                <div class="no-patients">
                    <p>No patients assigned yet.</p>
                </div>
            {:else}
                <div class="patients-table">
                    <table>
                        <thead>
                            <tr>
                                <th>Patient</th>
                                <th>Diagnosis</th>
                                <th>Assigned</th>
                                <th>Last Activity</th>
                                <th>Baseline</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {#each patients as patient}
                                <tr>
                                    <td>
                                        <div class="patient-name">
                                            {patient.full_name || patient.email}
                                        </div>
                                    </td>
                                    <td>{patient.diagnosis || 'N/A'}</td>
                                    <td>{formatDate(patient.assigned_at)}</td>
                                    <td>
                                        <span class="activity {patient.last_activity ? 'active' : 'inactive'}">
                                            {formatDate(patient.last_activity)}
                                        </span>
                                    </td>
                                    <td>
                                        <span class="badge {patient.baseline_completed ? 'complete' : 'pending'}">
                                            {patient.baseline_completed ? '✓ Complete' : 'Pending'}
                                        </span>
                                    </td>
                                    <td>
                                        <button 
                                            class="view-btn"
                                            on:click={() => viewPatient(patient.patient_id)}
                                        >
                                            View Details
                                        </button>
                                    </td>
                                </tr>
                            {/each}
                        </tbody>
                    </table>
                </div>
            {/if}
        </div>
    {/if}
</div>

<style>
    .doctor-dashboard {
        max-width: 1400px;
        margin: 0 auto;
        padding: 2rem;
    }
    
    header {
        margin-bottom: 2rem;
    }
    
    h1 {
        font-size: 2rem;
        color: #333;
        margin-bottom: 0.5rem;
    }
    
    header p {
        color: #666;
        font-size: 1.1rem;
    }
    
    .stats-cards {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin-bottom: 2rem;
    }
    
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
    }
    
    .stat-number {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    
    .stat-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    
    .patients-section {
        background: white;
        border-radius: 12px;
        padding: 2rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    h2 {
        margin-bottom: 1.5rem;
        color: #333;
    }
    
    .patients-table {
        overflow-x: auto;
    }
    
    table {
        width: 100%;
        border-collapse: collapse;
    }
    
    th {
        background: #f8f9fa;
        padding: 1rem;
        text-align: left;
        font-weight: 600;
        color: #555;
        border-bottom: 2px solid #e0e0e0;
    }
    
    td {
        padding: 1rem;
        border-bottom: 1px solid #e0e0e0;
    }
    
    tr:hover {
        background: #f8f9fa;
    }
    
    .patient-name {
        font-weight: 500;
        color: #333;
    }
    
    .activity.active {
        color: #28a745;
    }
    
    .activity.inactive {
        color: #999;
    }
    
    .badge {
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
    }
    
    .badge.complete {
        background: #d4edda;
        color: #155724;
    }
    
    .badge.pending {
        background: #fff3cd;
        color: #856404;
    }
    
    .view-btn {
        background: #667eea;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        cursor: pointer;
        font-weight: 500;
        transition: background 0.3s;
    }
    
    .view-btn:hover {
        background: #5568d3;
    }
    
    .no-patients {
        text-align: center;
        padding: 3rem;
        color: #999;
    }
    
    .loading, .error {
        text-align: center;
        padding: 2rem;
        font-size: 1.1rem;
    }
    
    .error {
        color: #c33;
    }
</style>
```

### 4.3 Create Patient Detail View for Doctors
**File**: `frontend-svelte/src/routes/doctor/patient/[id]/+page.svelte`

```svelte
<script>
    import { onMount } from 'svelte';
    import { page } from '$app/stores';
    import { user } from '$lib/stores.js';
    import { goto } from '$app/navigation';
    import api from '$lib/api.js';
    
    let patientId = $page.params.id;
    let patientData = null;
    let sessions = [];
    let loading = true;
    let error = '';
    
    onMount(async () => {
        if (!$user || $user.role !== 'doctor') {
            goto('/auth/login');
            return;
        }
        
        await loadPatientData();
    });
    
    async function loadPatientData() {
        try {
            // Load overview
            const overviewResponse = await api.get(
                `/api/doctor/${$user.id}/patient/${patientId}/overview`
            );
            patientData = overviewResponse.data;
            
            // Load sessions
            const sessionsResponse = await api.get(
                `/api/doctor/${$user.id}/patient/${patientId}/sessions?limit=20`
            );
            sessions = sessionsResponse.data.sessions;
            
        } catch (err) {
            error = 'Failed to load patient data';
            console.error(err);
        } finally {
            loading = false;
        }
    }
    
    function getDomainColor(domain) {
        const colors = {
            working_memory: '#667eea',
            attention: '#f093fb',
            flexibility: '#4facfe',
            planning: '#43e97b',
            processing_speed: '#fa709a',
            visual_scanning: '#feca57'
        };
        return colors[domain] || '#999';
    }
    
    function formatDate(dateStr) {
        return new Date(dateStr).toLocaleString();
    }
</script>

<div class="patient-detail">
    {#if loading}
        <div class="loading">Loading patient data...</div>
    {:else if error}
        <div class="error">{error}</div>
    {:else if patientData}
        <div class="header">
            <button on:click={() => goto('/doctor/dashboard')} class="back-btn">
                ← Back to Dashboard
            </button>
            <h1>{patientData.patient_info.full_name || patientData.patient_info.email}</h1>
            <p class="diagnosis">{patientData.patient_info.diagnosis || 'No diagnosis specified'}</p>
        </div>
        
        <!-- Overview Stats -->
        <div class="overview-grid">
            <div class="overview-card">
                <h3>Training Summary</h3>
                <div class="stat-row">
                    <span>Total Sessions:</span>
                    <strong>{patientData.training_summary.total_sessions}</strong>
                </div>
                <div class="stat-row">
                    <span>Current Streak:</span>
                    <strong>{patientData.training_summary.current_streak} days</strong>
                </div>
                <div class="stat-row">
                    <span>Longest Streak:</span>
                    <strong>{patientData.training_summary.longest_streak} days</strong>
                </div>
            </div>
            
            <div class="overview-card">
                <h3>Recent Performance (7 days)</h3>
                <div class="stat-row">
                    <span>Sessions:</span>
                    <strong>{patientData.recent_performance.sessions_last_7_days}</strong>
                </div>
                <div class="stat-row">
                    <span>Avg Score:</span>
                    <strong>{patientData.recent_performance.avg_score}/100</strong>
                </div>
                <div class="stat-row">
                    <span>Avg Accuracy:</span>
                    <strong>{patientData.recent_performance.avg_accuracy}%</strong>
                </div>
            </div>
            
            <div class="overview-card">
                <h3>Focus Areas</h3>
                <div class="focus-list">
                    <div>
                        <strong>Primary:</strong>
                        {#each patientData.focus_areas.primary as area}
                            <span class="focus-tag primary">{area}</span>
                        {/each}
                    </div>
                    <div>
                        <strong>Secondary:</strong>
                        {#each patientData.focus_areas.secondary as area}
                            <span class="focus-tag secondary">{area}</span>
                        {/each}
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Domain Performance -->
        <div class="section">
            <h2>Domain Performance</h2>
            <div class="domains-grid">
                {#each Object.entries(patientData.domain_performance) as [domain, stats]}
                    <div class="domain-card" style="border-left: 4px solid {getDomainColor(domain)}">
                        <h4>{domain.replace('_', ' ')}</h4>
                        <div class="domain-stats">
                            <div>
                                <span>Baseline:</span>
                                <strong>{stats.baseline_score?.toFixed(1) || 'N/A'}</strong>
                            </div>
                            <div>
                                <span>Current Avg:</span>
                                <strong>{stats.avg_score.toFixed(1)}</strong>
                            </div>
                            <div>
                                <span>Sessions:</span>
                                <strong>{stats.count}</strong>
                            </div>
                        </div>
                    </div>
                {/each}
            </div>
        </div>
        
        <!-- Recent Sessions -->
        <div class="section">
            <h2>Recent Training Sessions</h2>
            <div class="sessions-table">
                <table>
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Domain</th>
                            <th>Task</th>
                            <th>Difficulty</th>
                            <th>Score</th>
                            <th>Accuracy</th>
                            <th>RT (ms)</th>
                        </tr>
                    </thead>
                    <tbody>
                        {#each sessions as session}
                            <tr>
                                <td>{formatDate(session.completed_at)}</td>
                                <td>
                                    <span 
                                        class="domain-badge" 
                                        style="background: {getDomainColor(session.domain)}"
                                    >
                                        {session.domain}
                                    </span>
                                </td>
                                <td>{session.task_code || session.task_type}</td>
                                <td>Level {session.difficulty}</td>
                                <td><strong>{session.score}</strong></td>
                                <td>{session.accuracy}%</td>
                                <td>{session.reaction_time || 'N/A'}</td>
                            </tr>
                        {/each}
                    </tbody>
                </table>
            </div>
        </div>
    {/if}
</div>

<style>
    .patient-detail {
        max-width: 1400px;
        margin: 0 auto;
        padding: 2rem;
    }
    
    .header {
        margin-bottom: 2rem;
    }
    
    .back-btn {
        background: #f0f0f0;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        cursor: pointer;
        margin-bottom: 1rem;
    }
    
    h1 {
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }
    
    .diagnosis {
        color: #666;
        font-size: 1.1rem;
    }
    
    .overview-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 1rem;
        margin-bottom: 2rem;
    }
    
    .overview-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    .overview-card h3 {
        margin-bottom: 1rem;
        color: #333;
    }
    
    .stat-row {
        display: flex;
        justify-content: space-between;
        padding: 0.5rem 0;
        border-bottom: 1px solid #f0f0f0;
    }
    
    .focus-tag {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        margin: 0.25rem;
    }
    
    .focus-tag.primary {
        background: #fecaca;
        color: #991b1b;
    }
    
    .focus-tag.secondary {
        background: #fef3c7;
        color: #92400e;
    }
    
    .section {
        background: white;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
    }
    
    .section h2 {
        margin-bottom: 1.5rem;
    }
    
    .domains-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1rem;
    }
    
    .domain-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
    }
    
    .domain-card h4 {
        text-transform: capitalize;
        margin-bottom: 0.75rem;
        color: #333;
    }
    
    .domain-stats div {
        display: flex;
        justify-content: space-between;
        padding: 0.25rem 0;
    }
    
    .sessions-table {
        overflow-x: auto;
    }
    
    table {
        width: 100%;
        border-collapse: collapse;
    }
    
    th {
        background: #f8f9fa;
        padding: 0.75rem;
        text-align: left;
        font-weight: 600;
        border-bottom: 2px solid #e0e0e0;
    }
    
    td {
        padding: 0.75rem;
        border-bottom: 1px solid #e0e0e0;
    }
    
    .domain-badge {
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
    }
    
    .loading, .error {
        text-align: center;
        padding: 3rem;
        font-size: 1.1rem;
    }
    
    .error {
        color: #c33;
    }
</style>
```

---

## 🔧 STEP 5: Database Migration

Create migration script to add new tables:

**File**: `backend/create_doctor_tables.py`

```python
from sqlmodel import SQLModel, create_engine
from app.core.config import DATABASE_URL
from app.models.doctor import Doctor
from app.models.patient_assignment import PatientAssignment
from app.models.doctor_intervention import DoctorIntervention
from app.models.user import User

# Import all models to ensure they're registered
from app.models import *

engine = create_engine(DATABASE_URL)

def create_doctor_tables():
    """Create doctor-related tables"""
    print("Creating doctor tables...")
    SQLModel.metadata.create_all(engine)
    print("✅ Doctor tables created successfully!")

if __name__ == "__main__":
    create_doctor_tables()
```

Run: `python backend/create_doctor_tables.py`

---

## 📊 STEP 6: Update User Store (Frontend)

**File**: `frontend-svelte/src/lib/stores.js`

```javascript
import { writable } from 'svelte/store';

// Load user from localStorage on initialization
const storedUser = typeof window !== 'undefined' 
    ? JSON.parse(localStorage.getItem('user') || 'null')
    : null;

export const user = writable(storedUser);

// Subscribe to user changes and update localStorage
if (typeof window !== 'undefined') {
    user.subscribe(value => {
        if (value) {
            localStorage.setItem('user', JSON.stringify(value));
        } else {
            localStorage.removeItem('user');
        }
    });
}
```

---

## ✅ TESTING CHECKLIST

### Backend Tests:
1. ✅ Register a new doctor account
2. ✅ Login as doctor (should require verification)
3. ✅ Assign a patient to a doctor
4. ✅ Fetch doctor's patient list
5. ✅ Get patient overview with analytics
6. ✅ Get patient session history
7. ✅ Add clinical intervention/note

### Frontend Tests:
1. ✅ Toggle between patient/doctor login
2. ✅ Login as doctor → redirect to doctor dashboard
3. ✅ View patient list
4. ✅ Click patient → view detailed analytics
5. ✅ Check all performance metrics display correctly

---

## 🚀 DEPLOYMENT NOTES

### Security Considerations:
1. **Role-Based Access Control**: Always verify doctor has access to patient
2. **Patient Consent**: Require `consent_to_share = True` before assignment
3. **Doctor Verification**: Implement admin panel to verify doctor licenses
4. **HIPAA Compliance** (if applicable): Add encryption, audit logs, data retention policies
5. **Two-Factor Authentication**: Consider adding 2FA for doctor accounts

### Future Enhancements:
1. **Clinical Report Generation**: PDF export of patient progress
2. **Doctor Notes Timeline**: Chronological view of interventions
3. **Notifications**: Alert doctor when patient performance declines
4. **Telemedicine Integration**: Video consultation scheduling
5. **Prescription/Recommendation System**: Formal treatment plan adjustments
6. **Multi-Facility Support**: Hospital/clinic organization structure

---

## 📝 SUMMARY

This implementation adds:
- ✅ Separate doctor authentication system
- ✅ Patient-doctor assignment mechanism
- ✅ Comprehensive patient monitoring dashboard
- ✅ Detailed performance analytics
- ✅ Session history tracking
- ✅ Clinical intervention recording
- ✅ Role-based access control

**Estimated Development Time**: 3-5 days for full implementation
**Impact for Research**: Enables clinical trials, provider collaboration, and healthcare integration
