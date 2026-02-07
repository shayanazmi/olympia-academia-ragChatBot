import sqlite3
import datetime
import logging
from pathlib import Path

# --- PATH CONFIGURATION ---
PROJECT_ROOT = Path("D:/college/Olympia Academia/oa_chatbot/olympia-academia")
DATA_DIR = PROJECT_ROOT / "data"
DB_DIR = DATA_DIR / "db"

# Ensure directory exists
DB_DIR.mkdir(parents=True, exist_ok=True)

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
    init_limits_db() # Ensure DB exists
    
    today = datetime.date.today().isoformat()
    
    try:
        conn = sqlite3.connect(DB_FILE, timeout=10) # Timeout prevents locking issues
        c = conn.cursor()
        
        # Check current count
        c.execute("SELECT query_count FROM usage_logs WHERE user_id=? AND date_str=?", (user_id, today))
        result = c.fetchone()
        
        if result:
            count = result[0]
            if count >= max_limit:
                conn.close()
                return False, count # Limit Reached
            
            # Increment Usage
            new_count = count + 1
            c.execute("UPDATE usage_logs SET query_count=? WHERE user_id=? AND date_str=?", (new_count, user_id, today))
        else:
            # First query of the day for this user
            new_count = 1
            c.execute("INSERT INTO usage_logs VALUES (?, ?, ?)", (user_id, today, new_count))
        
        conn.commit()
        conn.close()
        return True, new_count

    except Exception as e:
        logging.error(f"Limit Check Error: {e}")
        # In case of DB error, allow access (fail open) or deny (fail closed). 
        # Here we fail open to avoid user frustration during bugs.
        return True, 0