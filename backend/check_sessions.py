from sqlalchemy import create_engine, text

engine = create_engine('postgresql://postgres:postgres@localhost:5432/neurobloom_db')

with engine.connect() as conn:
    result = conn.execute(text('''
        SELECT id, user_id, domain, score, training_plan_id, created_at 
        FROM training_sessions 
        ORDER BY created_at DESC 
        LIMIT 10
    '''))
    
    print("Recent training sessions:")
    print("=" * 80)
    for row in result:
        print(f"ID: {row.id}, Domain: {row.domain}, Score: {row.score:.1f}%, Plan: {row.training_plan_id}, Time: {row.created_at}")
