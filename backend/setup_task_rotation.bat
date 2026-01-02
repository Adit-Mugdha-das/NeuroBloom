@echo off
REM Task Rotation Setup Script
REM Run this to set up the smart task rotation system

echo ========================================
echo NeuroBloom Task Rotation Setup
echo ========================================
echo.

echo [1/3] Activating Python environment...
cd d:\NeuroBloom\backend
call venv\Scripts\activate.bat

echo.
echo [2/3] Seeding cognitive tasks database...
python seed_cognitive_tasks.py

echo.
echo [3/3] Verifying setup...
python -c "from sqlmodel import Session, select; from app.core.config import engine; from app.models.cognitive_task import CognitiveTask; session = Session(engine); count = len(session.exec(select(CognitiveTask)).all()); print(f'\n✅ SUCCESS! {count} tasks loaded in database\n')"

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Restart your backend server
echo 2. Test /training-plan/{user_id}/next-tasks endpoint
echo 3. Check TASK_ROTATION_IMPLEMENTATION_GUIDE.md for details
echo.
pause
