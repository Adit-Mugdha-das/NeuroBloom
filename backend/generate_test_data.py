"""
Quick Test Data Generator for Development
Run this to instantly populate your training plan with completed sessions
"""
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import random

DATABASE_URL = "postgresql://postgres:2107118@localhost:5432/neurobloom_db"
engine = create_engine(DATABASE_URL)

def generate_test_sessions(num_sessions=2, user_id=2, training_plan_id=1):
    """
    Generate completed training sessions with realistic data.
    Each session = 4 tasks (one from each domain)
    """
    
    domains = ['working_memory', 'processing_speed', 'attention', 'flexibility']
    task_types = ['n_back', 'reaction_time', 'continuous_performance', 'task_switching']
    
    with engine.connect() as conn:
        print(f"\n🚀 Generating {num_sessions} test sessions...")
        print("=" * 60)
        
        for session_num in range(num_sessions):
            # Sessions created over past few days
            base_time = datetime.utcnow() - timedelta(days=num_sessions - session_num - 1, hours=random.randint(0, 12))
            
            print(f"\n📝 Session #{session_num + 1} - {base_time.strftime('%Y-%m-%d %H:%M')}")
            
            for i, (domain, task_type) in enumerate(zip(domains, task_types)):
                # Generate realistic scores
                score = random.uniform(60, 95)
                accuracy = random.uniform(70, 100)
                avg_rt = random.uniform(400, 1200)
                consistency = random.uniform(60, 95)
                errors = random.randint(0, 10)
                difficulty = random.randint(3, 8)
                
                # Each task a few minutes apart
                task_time = base_time + timedelta(minutes=i * 3)
                
                # Insert training session
                conn.execute(text("""
                    INSERT INTO training_sessions 
                    (user_id, training_plan_id, domain, task_type, score, accuracy, 
                     average_reaction_time, consistency, errors, difficulty_level, 
                     difficulty_before, difficulty_after, duration, completed,
                     adaptation_reason, raw_data, created_at)
                    VALUES 
                    (:user_id, :plan_id, :domain, :task_type, :score, :accuracy,
                     :avg_rt, :consistency, :errors, :difficulty,
                     :difficulty, :difficulty, 5, true,
                     'Test data', '{}', :created_at)
                """), {
                    'user_id': user_id,
                    'plan_id': training_plan_id,
                    'domain': domain,
                    'task_type': task_type,
                    'score': score,
                    'accuracy': accuracy,
                    'avg_rt': avg_rt,
                    'consistency': consistency,
                    'errors': errors,
                    'difficulty': difficulty,
                    'created_at': task_time
                })
                
                print(f"  ✓ {domain}: {score:.1f}% (Difficulty {difficulty})")
            
            conn.commit()
        
        # Update training plan stats
        total_sessions = num_sessions
        last_session_date = datetime.utcnow()
        
        conn.execute(text("""
            UPDATE training_plans 
            SET total_sessions_completed = :total,
                last_session_date = :last_date,
                current_session_tasks_completed = '[]',
                current_session_number = :next_session,
                current_streak = 1,
                longest_streak = 1,
                total_training_days = 1
            WHERE id = :plan_id
        """), {
            'total': total_sessions,
            'last_date': last_session_date,
            'next_session': total_sessions + 1,
            'plan_id': training_plan_id
        })
        
        conn.commit()
        
        print("\n" + "=" * 60)
        print(f"✅ Successfully generated {num_sessions} sessions!")
        print(f"📊 Total sessions: {total_sessions}")
        print(f"🔥 Streak: 1 day")
        print("\n💡 Now you can test:")
        print("   - Session Summary page")
        print("   - Progress graphs")
        print("   - Streak tracking")
        print("   - Performance metrics")
        print("\n🔄 Run this script anytime to add more test data!")

def clear_test_data(training_plan_id=1):
    """Clear all test training sessions"""
    with engine.connect() as conn:
        result = conn.execute(text("""
            DELETE FROM training_sessions 
            WHERE training_plan_id = :plan_id
        """), {'plan_id': training_plan_id})
        
        conn.execute(text("""
            UPDATE training_plans 
            SET total_sessions_completed = 0,
                current_session_tasks_completed = '[]',
                current_session_number = 1,
                current_streak = 0,
                longest_streak = 0,
                total_training_days = 0,
                last_session_date = NULL
            WHERE id = :plan_id
        """), {'plan_id': training_plan_id})
        
        conn.commit()
        
        print(f"🗑️  Cleared {result.rowcount} test sessions")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'clear':
        clear_test_data()
    else:
        # Default: generate 2 sessions (8 tasks total)
        num = int(sys.argv[1]) if len(sys.argv) > 1 else 2
        generate_test_sessions(num_sessions=num)
