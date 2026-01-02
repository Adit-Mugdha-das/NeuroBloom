from sqlmodel import Session, text
from app.core.config import engine

with Session(engine) as session:
    # Reset the current session for user 2 using raw SQL
    result = session.exec(text("UPDATE training_plans SET current_session_tasks_completed = '[]' WHERE user_id = 2 AND is_active = true RETURNING id, current_session_tasks_completed"))
    row = result.first()
    session.commit()
    
    if row:
        print(f'Reset session for plan ID: {row[0]}')
        print(f'New value: {row[1]}')
        print('Session reset successfully! Refresh the training page.')
    else:
        print('No active training plan found')




