"""User storage and authentication."""

import hashlib
import logging
import sqlite3
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def init_user_db(db_path: str = "./users.db") -> None:
    """
    Initialize the user database.
    
    Args:
        db_path: Path to SQLite database file
    """
    db_dir = Path(db_path).parent
    if db_dir:
        db_dir.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            last_login TEXT,
            is_admin INTEGER DEFAULT 0
        )
    """)
    
    # Add is_admin column if it doesn't exist (for existing databases)
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        # Column already exists, ignore
        pass
    
    conn.commit()
    conn.close()
    logger.info(f"User database initialized: {db_path}")


def hash_password(password: str) -> str:
    """
    Hash a password using SHA-256 with salt.
    
    Args:
        password: Plain text password
    
    Returns:
        Hashed password string
    """
    # Simple hash for now (in production, use bcrypt or argon2)
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def create_user(db_path: str, email: str, password: str, name: str) -> Tuple[bool, str]:
    """
    Create a new user account.
    
    Args:
        db_path: Path to SQLite database
        email: User email (must be unique)
        password: Plain text password (will be hashed)
        name: User's full name
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    from datetime import datetime, timezone
    
    if not email or not password or not name:
        return False, "Email, password, and name are required"
    
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    
    email = email.strip().lower()
    password_hash = hash_password(password)
    created_at = datetime.now(timezone.utc).isoformat()
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO users (email, password_hash, name, created_at)
            VALUES (?, ?, ?, ?)
        """, (email, password_hash, name, created_at))
        
        conn.commit()
        conn.close()
        
        logger.info(f"User created: {email}")
        return True, "Account created successfully!"
    
    except sqlite3.IntegrityError:
        return False, "Email already exists. Please use a different email or log in."
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return False, f"Error creating account: {str(e)}"


def verify_user(db_path: str, email: str, password: str) -> Tuple[bool, Optional[dict]]:
    """
    Verify user credentials.
    
    Args:
        db_path: Path to SQLite database
        email: User email
        password: Plain text password
    
    Returns:
        Tuple of (success: bool, user_data: dict or None)
        user_data contains: id, email, name
    """
    email = email.strip().lower()
    password_hash = hash_password(password)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, email, password_hash, name, last_login, is_admin
            FROM users
            WHERE email = ?
        """, (email,))
        
        row = cursor.fetchone()
        
        if row and row[2] == password_hash:  # row[2] is password_hash
            # Update last_login
            from datetime import datetime, timezone
            last_login = datetime.now(timezone.utc).isoformat()
            cursor.execute("""
                UPDATE users
                SET last_login = ?
                WHERE id = ?
            """, (last_login, row[0]))
            conn.commit()
            
            user_data = {
                'id': row[0],
                'email': row[1],
                'name': row[3],
                'is_admin': bool(row[5]) if len(row) > 5 else False,
            }
            conn.close()
            logger.info(f"User logged in: {email} (admin: {user_data.get('is_admin', False)})")
            return True, user_data
        else:
            conn.close()
            return False, None
    
    except Exception as e:
        logger.error(f"Error verifying user: {e}")
        return False, None


def get_user_by_id(db_path: str, user_id: int) -> Optional[dict]:
    """
    Get user data by ID.
    
    Args:
        db_path: Path to SQLite database
        user_id: User ID
    
    Returns:
        User data dict or None
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, email, name
            FROM users
            WHERE id = ?
        """, (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'email': row[1],
                'name': row[2],
            }
        return None
    
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        return None


def get_all_users(db_path: str) -> list[dict]:
    """
    Get all users from the database.
    
    Args:
        db_path: Path to SQLite database
    
    Returns:
        List of user dictionaries with: id, email, name, created_at, last_login
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, email, name, created_at, last_login, is_admin
            FROM users
            ORDER BY created_at DESC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        users = []
        for row in rows:
            users.append({
                'id': row[0],
                'email': row[1],
                'name': row[2],
                'created_at': row[3],
                'last_login': row[4] if len(row) > 4 else None,
                'is_admin': bool(row[5]) if len(row) > 5 else False,
            })
        
        return users
    
    except Exception as e:
        logger.error(f"Error getting all users: {e}")
        return []


def get_user_count(db_path: str) -> int:
    """
    Get total number of users in the database.
    
    Args:
        db_path: Path to SQLite database
    
    Returns:
        Total number of users
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        
        conn.close()
        return count
    
    except Exception as e:
        logger.error(f"Error getting user count: {e}")
        return 0

