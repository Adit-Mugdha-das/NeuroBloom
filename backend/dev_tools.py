"""
Quick Development Commands

Usage:
    python dev_tools.py generate [num_sessions]  - Generate test sessions (default: 2)
    python dev_tools.py clear                     - Clear all test data
    python dev_tools.py complete                  - Complete current session instantly
    python dev_tools.py streak [days]             - Set streak to X days
"""
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import random
import sys

DATABASE_URL = "postgresql://postgres:2107118@localhost:5432/neurobloom_db"
engine = create_engine(DATABASE_URL)

def generate_sessions(num_sessions=2):
    """Generate completed test sessions"""
    domains = ['working_memory', 'processing_speed', 'attention', 'flexibility']
    task_types = ['n_back', 'reaction_time', 'continuous_performance', 'task_switching']
    
    with engine.connect() as conn:
        for session_num in range(num_sessions):
            base_time = datetime.utcnow() - timedelta(days=num_sessions - session_num - 1)
            
            for i, (domain, task_type) in enumerate(zip(domains, task_types)):
                score = random.uniform(60, 95)
                accuracy = random.uniform(70, 100)
                
                conn.execute(text("""
                    INSERT INTO training_sessions 
                    (user_id, training_plan_id, domain, task_type, score, accuracy, 
                     average_reaction_time, consistency, errors, difficulty_level, 
                     difficulty_before, difficulty_after, duration, completed, created_at)
                    VALUES (2, 1, :domain, :task_type, :score, :accuracy, 500, 80, 2, 5, 5, 5, 5, true, :time)
                """), {
                    'domain': domain,
                    'task_type': task_type,
                    'score': score,
                    'accuracy': accuracy,
                    'time': base_time + timedelta(minutes=i * 3)
                })
        
        conn.execute(text("""
            UPDATE training_plans 
            SET total_sessions_completed = total_sessions_completed + :num,
                current_session_tasks_completed = '[]',
                last_session_date = :now
            WHERE id = 1
        """), {'num': num_sessions, 'now': datetime.utcnow()})
        
        conn.commit()
        print(f"✅ Generated {num_sessions} sessions")

def complete_current_session():
    """Instantly complete the current session"""
    domains = ['working_memory', 'processing_speed', 'attention', 'flexibility']
    task_types = ['n_back', 'reaction_time', 'continuous_performance', 'task_switching']
    
    with engine.connect() as conn:
        # Get current completed tasks
        result = conn.execute(text("""
            SELECT current_session_tasks_completed FROM training_plans WHERE id = 1
        """)).fetchone()
        
        if not result:
            print("❌ Training plan not found")
            return
        
        completed = eval(result[0]) if result[0] != '[]' else []
        
        # Add missing tasks
        now = datetime.utcnow()
        for i, (domain, task_type) in enumerate(zip(domains, task_types)):
            if domain not in completed:
                conn.execute(text("""
                    INSERT INTO training_sessions 
                    (user_id, training_plan_id, domain, task_type, score, accuracy, 
                     average_reaction_time, consistency, errors, difficulty_level, 
                     difficulty_before, difficulty_after, duration, completed, created_at)
                    VALUES (2, 1, :domain, :task_type, 85, 90, 600, 85, 1, 5, 5, 5, 5, true, :time)
                """), {
                    'domain': domain,
                    'task_type': task_type,
                    'time': now + timedelta(seconds=i * 10)
                })
                print(f"✓ Completed {domain}")
        
        # Mark session complete
        conn.execute(text("""
            UPDATE training_plans 
            SET total_sessions_completed = total_sessions_completed + 1,
                current_session_tasks_completed = '[]',
                current_session_number = current_session_number + 1,
                last_session_date = :now,
                current_streak = 1,
                total_training_days = COALESCE(total_training_days, 0) + 1
            WHERE id = 1
        """), {'now': now})
        
        conn.commit()
        print("✅ Session completed! Go to /session-summary to see results")

def set_streak(days):
    """Set streak to specific number of days"""
    with engine.connect() as conn:
        conn.execute(text("""
            UPDATE training_plans 
            SET current_streak = :days,
                longest_streak = GREATEST(longest_streak, :days),
                total_training_days = GREATEST(total_training_days, :days)
            WHERE id = 1
        """), {'days': days})
        conn.commit()
        print(f"✅ Streak set to {days} days 🔥")

def clear_all():
    """Clear all test data"""
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM training_sessions WHERE training_plan_id = 1"))
        conn.execute(text("""
            UPDATE training_plans 
            SET total_sessions_completed = 0,
                current_session_tasks_completed = '[]',
                current_session_number = 1,
                current_streak = 0,
                longest_streak = 0,
                total_training_days = 0
            WHERE id = 1
        """))
        conn.commit()
        print("✅ All test data cleared")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'generate':
        num = int(sys.argv[2]) if len(sys.argv) > 2 else 2
        generate_sessions(num)
    elif command == 'complete':
        complete_current_session()
    elif command == 'streak':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        set_streak(days)
    elif command == 'clear':
        clear_all()
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
