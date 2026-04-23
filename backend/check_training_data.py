from sqlalchemy import text

from app.core.config import engine

with engine.connect() as conn:
    # Check training plan
    print("=" * 80)
    print("TRAINING PLAN:")
    print("=" * 80)
    result = conn.execute(text('''
        SELECT id, user_id, current_session_number, 
               total_sessions_completed, current_session_tasks_completed,
               primary_focus, secondary_focus, recommended_tasks
        FROM training_plans 
        WHERE is_active = true
        ORDER BY created_at DESC 
        LIMIT 1
    '''))
    for row in result:
        print(f"Plan ID: {row.id}, User: {row.user_id}")
        print(f"Session: {row.current_session_number}, Total: {row.total_sessions_completed}")
        print(f"Completed tasks: {row.current_session_tasks_completed}")
        print(f"Primary focus: {row.primary_focus}")
        print(f"Secondary focus: {row.secondary_focus}")
        print(f"Recommended tasks: {row.recommended_tasks}")
    
    # Check training sessions
    print("\n" + "=" * 80)
    print("TRAINING SESSIONS:")
    print("=" * 80)
    result = conn.execute(text('''
        SELECT id, user_id, domain, task_type, score, 
               training_plan_id, created_at
        FROM training_sessions 
        ORDER BY created_at DESC 
        LIMIT 10
    '''))
    
    sessions = list(result)
    if sessions:
        for row in sessions:
            print(f"{row.created_at.strftime('%H:%M:%S')} - Domain: {row.domain:20s} Task: {row.task_type:20s} Score: {row.score:5.1f}% Plan: {row.training_plan_id}")
    else:
        print("No training sessions found!")
    
    print(f"\nTotal sessions: {len(sessions)}")
