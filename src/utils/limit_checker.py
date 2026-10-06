import sqlite3
import datetime
import logging
from pathlib import Path
from src.utils.config import DB_DIR

# Database file
DB_FILE = DB_DIR / "user_limits.db"

def init_limits_db():
    """Creates the SQLite table if it doesn't exist."""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS usage_logs 
                     (user_id TEXT, date_str TEXT, query_count INTEGER, PRIMARY KEY (user_id, date_str))''')
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Database Initialization Error: {e}")

def check_and_update_limit(user_id, max_limit=10):
    """
    Checks if a user has exceeded their daily limit.
    Returns: (allowed: bool, current_count: int)
    """
    init_limits_db()
    today = datetime.date.today().isoformat()
    
    try:
        conn = sqlite3.connect(DB_FILE, timeout=10)
        c = conn.cursor()
        
        c.execute("SELECT query_count FROM usage_logs WHERE user_id=? AND date_str=?", (user_id, today))
        result = c.fetchone()
        
        if result:
            count = result[0]
            if count >= max_limit:
                conn.close()
                return False, count
            
            new_count = count + 1
            c.execute("UPDATE usage_logs SET query_count=? WHERE user_id=? AND date_str=?", (new_count, user_id, today))
        else:
            new_count = 1
            c.execute("INSERT INTO usage_logs VALUES (?, ?, ?)", (user_id, today, new_count))
        
        conn.commit()
        conn.close()
        return True, new_count

    except Exception as e:
        logging.error(f"Limit Check Error: {e}")
        return True, 0
