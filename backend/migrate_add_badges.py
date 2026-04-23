"""
Migration script to add user_badges table
Run this script to add badge tracking to the database
"""

import psycopg2
from psycopg2 import sql

from app.core.config import settings

def migrate():
    """Add user_badges table"""
    conn = None
    try:
        # Connect to database
        conn = psycopg2.connect(settings.DATABASE_URL)
        cur = conn.cursor()
        
        print("Creating user_badges table...")
        
        # Create user_badges table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_badges (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
                badge_id VARCHAR(100) NOT NULL,
                earned_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                progress INTEGER NOT NULL DEFAULT 0,
                UNIQUE(user_id, badge_id)
            );
        """)
        
        # Create index for faster queries
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_badges_user_id ON user_badges(user_id);
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_badges_badge_id ON user_badges(badge_id);
        """)
        
        conn.commit()
        print("✅ user_badges table created successfully!")
        print("✅ Indexes created successfully!")
        
        # Verify the table was created
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'user_badges'
            ORDER BY ordinal_position;
        """)
        
        print("\nTable structure:")
        for row in cur.fetchall():
            print(f"  - {row[0]}: {row[1]}")
        
        cur.close()
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    migrate()
