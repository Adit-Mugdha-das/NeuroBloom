# 🏥 Doctor Portal - Setup & Testing Guide

## ✅ Implementation Complete!

All components of the doctor portal have been implemented. Follow these steps to set up and test the feature.

---

## 📋 Step 1: Run Database Migration

First, create the new doctor-related tables in your database:

```bash
cd backend
python migrate_add_doctor_portal.py
```

You should see output like:
```
✅ Doctor table - CREATED
✅ PatientAssignment table - CREATED
✅ DoctorIntervention table - CREATED
✅ User table - UPDATED
```

---

## 🚀 Step 2: Restart Backend Server

```bash
cd backend
uvicorn app.main:app --reload
```

The server should start without errors. Check the console for:
- No import errors
- All routers registered
- Database connection successful

---

## 🧪 Step 3: Test Doctor Registration

### Option A: Using API Tool (Postman/Thunder Client)

**POST** `http://localhost:8000/api/auth/doctor/register`

**Body** (JSON):
```json
{
  "email": "doctor@example.com",
  "password": "password123",
  "full_name": "Dr. Sarah Johnson",
  "license_number": "MD12345",
  "specialization": "Neurologist",
  "institution": "City Hospital"
}
```

**Expected Response**:
```json
{
  "id": 1,
  "email": "doctor@example.com",
  "full_name": "Dr. Sarah Johnson",
  "specialization": "Neurologist",
  "institution": "City Hospital",
  "is_verified": false,
  "is_active": true,
  "created_at": "2026-01-09T..."
}
```

### Option B: Using Python Script

Create `backend/test_doctor_registration.py`:
```python
import requests

API_URL = "http://localhost:8000/api"

# Register doctor
response = requests.post(f"{API_URL}/auth/doctor/register", json={
    "email": "doctor@test.com",
    "password": "test123",
    "full_name": "Dr. Test Doctor",
    "specialization": "Neuropsychologist",
    "institution": "Test Hospital"
})

print("Registration:", response.json())
```

Run: `python backend/test_doctor_registration.py`

---

## 🔑 Step 4: Verify Doctor Account

Since doctors require admin approval, you need to manually verify the account:

### Option A: Using PostgreSQL GUI (pgAdmin, DBeaver)

1. Connect to your database
2. Find the `doctors` table
3. Locate your doctor record
4. Update: `is_verified = TRUE`

### Option B: Using SQL Command

```sql
UPDATE doctors 
SET is_verified = TRUE 
WHERE email = 'doctor@example.com';
```

### Option C: Using Python Script

Create `backend/verify_doctor.py`:
```python
from sqlmodel import Session, select
from app.core.config import engine
from app.models.doctor import Doctor

with Session(engine) as session:
    doctor = session.exec(
        select(Doctor).where(Doctor.email == "doctor@example.com")
    ).first()
    
    if doctor:
        doctor.is_verified = True
        session.add(doctor)
        session.commit()
        print(f"✅ Doctor {doctor.email} verified!")
    else:
        print("❌ Doctor not found")
```

Run: `python backend/verify_doctor.py`

---

## 🔐 Step 5: Test Doctor Login

### Via API:

**POST** `http://localhost:8000/api/auth/doctor/login`

**Body**:
```json
{
  "email": "doctor@example.com",
  "password": "password123"
}
```

**Expected Response**:
```json
{
  "message": "Login successful",
  "email": "doctor@example.com",
  "id": 1,
  "role": "doctor",
  "full_name": "Dr. Sarah Johnson",
  "is_verified": true
}
```

### Via Frontend:

1. Start frontend: `cd frontend-svelte && npm run dev`
2. Go to `http://localhost:5173/login`
3. Click **"👨‍⚕️ Doctor"** button
4. Enter doctor credentials
5. Click "Login as Doctor"
6. Should redirect to `/doctor/dashboard`

---

## 👥 Step 6: Create Test Patient

We need a patient to assign to the doctor.

**POST** `http://localhost:8000/api/auth/register`

**Body**:
```json
{
  "email": "patient@example.com",
  "password": "patient123"
}
```

---

## ✅ Step 7: Enable Patient Consent

Before a doctor can access patient data, the patient must give consent.

### Option A: SQL Update
```sql
UPDATE user 
SET consent_to_share = TRUE,
    full_name = 'John Doe',
    diagnosis = 'RRMS'
WHERE email = 'patient@example.com';
```

### Option B: Python Script

Create `backend/update_patient_consent.py`:
```python
from sqlmodel import Session, select
from app.core.config import engine
from app.models.user import User

with Session(engine) as session:
    patient = session.exec(
        select(User).where(User.email == "patient@example.com")
    ).first()
    
    if patient:
        patient.consent_to_share = True
        patient.full_name = "John Doe"
        patient.diagnosis = "RRMS"
        session.add(patient)
        session.commit()
        print(f"✅ Patient {patient.email} updated!")
    else:
        print("❌ Patient not found")
```

---

## 🔗 Step 8: Assign Patient to Doctor

**POST** `http://localhost:8000/api/doctor/1/assign-patient`

**Headers**:
```
Content-Type: application/json
```

**Body**:
```json
{
  "patient_email": "patient@example.com",
  "diagnosis": "Relapsing-Remitting Multiple Sclerosis (RRMS)",
  "treatment_goal": "Improve working memory and processing speed",
  "notes": "Patient reports difficulty with multitasking"
}
```

**Expected Response**:
```json
{
  "message": "Patient assigned successfully",
  "assignment_id": 1,
  "patient_email": "patient@example.com"
}
```

---

## 📊 Step 9: View Patient List

**GET** `http://localhost:8000/api/doctor/1/patients`

**Expected Response**:
```json
{
  "patients": [
    {
      "patient_id": 1,
      "email": "patient@example.com",
      "full_name": "John Doe",
      "diagnosis": "Relapsing-Remitting Multiple Sclerosis (RRMS)",
      "assigned_at": "2026-01-09T...",
      "last_activity": null,
      "baseline_completed": false,
      "treatment_goal": "Improve working memory and processing speed"
    }
  ],
  "total": 1
}
```

---

## 🌐 Step 10: Test Full Frontend Workflow

1. **Login as Doctor**
   - Go to: `http://localhost:5173/login`
   - Select "👨‍⚕️ Doctor"
   - Login with doctor credentials
   - Should redirect to `/doctor/dashboard`

2. **View Dashboard**
   - See total patients count
   - See patient list table
   - Verify patient appears in the list

3. **View Patient Details**
   - Click "View Details" on a patient
   - Should navigate to `/doctor/patient/1`
   - See patient overview, stats, and session history

4. **Test Navigation**
   - Click "← Back to Dashboard"
   - Should return to doctor dashboard

---

## 🧪 Step 11: Test Patient Analytics (After Patient Completes Training)

For this test, the patient needs to have completed some training sessions.

**As Patient:**
1. Login as patient
2. Complete baseline assessment (if not done)
3. Complete a few training sessions

**As Doctor:**
1. Login as doctor
2. Go to patient detail page
3. You should now see:
   - Baseline scores
   - Domain performance stats
   - Recent session history
   - Training summary

---

## 📝 Step 12: Test Adding Clinical Intervention

**POST** `http://localhost:8000/api/doctor/1/patient/1/intervention`

**Body**:
```json
{
  "intervention_type": "recommendation",
  "description": "Recommend increasing focus on working memory tasks. Patient shows good engagement."
}
```

**Expected Response**:
```json
{
  "message": "Intervention recorded successfully",
  "intervention_id": 1
}
```

---

## ✅ Full Testing Checklist

### Backend Tests:
- [ ] Doctor registration endpoint works
- [ ] Doctor must be verified to login
- [ ] Doctor login returns correct role
- [ ] Patient assignment requires consent
- [ ] Get patients list works
- [ ] Get patient overview works
- [ ] Get patient sessions works
- [ ] Add intervention works
- [ ] Cannot access patient without assignment

### Frontend Tests:
- [ ] Login page shows patient/doctor toggle
- [ ] Toggle switches between modes
- [ ] Doctor login redirects to `/doctor/dashboard`
- [ ] Patient login redirects to `/dashboard`
- [ ] Doctor dashboard shows patient statistics
- [ ] Patient list displays correctly
- [ ] Click patient navigates to detail view
- [ ] Patient detail shows all analytics
- [ ] Back button works
- [ ] Logout and login again preserves role

---

## 🐛 Troubleshooting

### Error: "Account pending verification"
**Solution**: Run the verification script to set `is_verified = TRUE`

### Error: "Patient has not consented"
**Solution**: Update patient's `consent_to_share = TRUE`

### Error: "No access to this patient"
**Solution**: Ensure patient is assigned to doctor via `/assign-patient` endpoint

### Frontend doesn't show doctor dashboard
**Solution**: 
1. Check browser console for errors
2. Verify localStorage has user with `role: "doctor"`
3. Clear browser cache and localStorage
4. Login again

### Database migration errors
**Solution**:
1. Check DATABASE_URL in `backend/app/core/config.py`
2. Ensure PostgreSQL is running
3. Verify you have write permissions
4. Check if tables already exist (migration is idempotent)

---

## 🎉 Success Criteria

You've successfully implemented the doctor portal when:

✅ Doctor can register and login (after verification)  
✅ Doctor dashboard shows patient list  
✅ Doctor can view individual patient analytics  
✅ Patient detail page shows:
- Training summary
- Recent performance
- Domain breakdown
- Session history
- Baseline scores (if completed)  
✅ Navigation works smoothly  
✅ Role-based authentication prevents unauthorized access

---

## 🚀 Next Steps

### Optional Enhancements:

1. **Admin Panel**: Create interface to verify doctors
2. **Email Notifications**: Notify patients when assigned to doctor
3. **Reports Export**: Generate PDF reports for patients
4. **Charts & Graphs**: Add visualizations to patient detail page
5. **Intervention Timeline**: Show chronological list of doctor notes
6. **Patient Search**: Add search/filter to doctor dashboard
7. **Bulk Operations**: Assign multiple patients at once
8. **Doctor Profile**: Allow doctors to edit their profile

---

## 📞 Support

If you encounter issues:
1. Check server logs for errors
2. Verify database schema matches models
3. Ensure all dependencies are installed
4. Check browser console for frontend errors

---

**🎊 Congratulations! Your doctor portal is now fully functional!**
