"""User activity storage for searches and resume uploads."""

import logging
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

# Directory to store uploaded resumes - use absolute path relative to project root
def get_resumes_dir():
    """Get the absolute path to the resumes directory."""
    # Get the project root (parent of 'app' directory)
    # __file__ is at app/storage/user_activity.py
    # Go up: storage -> app -> project root
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent  # app/storage -> app -> project root
    resumes_dir = project_root / "resumes"
    resumes_dir.mkdir(parents=True, exist_ok=True)
    return resumes_dir


def init_activity_db(db_path: str = "./user_activity.db") -> None:
    """
    Initialize the user activity database.
    
    Args:
        db_path: Path to SQLite database file
    """
    db_dir = Path(db_path).parent
    if db_dir:
        db_dir.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create search_history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            user_email TEXT NOT NULL,
            role TEXT,
            time_window TEXT,
            location TEXT,
            remote_only INTEGER DEFAULT 0,
            searched_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Create resume_uploads table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resume_uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            user_email TEXT NOT NULL,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            uploaded_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_search_user_id ON search_history(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_search_searched_at ON search_history(searched_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_resume_user_id ON resume_uploads(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_resume_uploaded_at ON resume_uploads(uploaded_at)")
    
    conn.commit()
    conn.close()
    logger.info(f"User activity database initialized: {db_path}")


def save_search(db_path: str, user_id: int, user_email: str, role: str, 
                time_window: str, location: str, remote_only: bool) -> None:
    """
    Save a user's search to the database.
    
    Args:
        db_path: Path to SQLite database
        user_id: User ID
        user_email: User email
        role: Job role/keywords searched
        time_window: Time window selected
        location: Location filter
        remote_only: Whether remote only was selected
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        searched_at = datetime.now(timezone.utc).isoformat()
        
        cursor.execute("""
            INSERT INTO search_history 
            (user_id, user_email, role, time_window, location, remote_only, searched_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, user_email, role, time_window, location, 1 if remote_only else 0, searched_at))
        
        conn.commit()
        conn.close()
        logger.info(f"Search saved for user {user_email}: {role}")
    
    except Exception as e:
        logger.error(f"Error saving search: {e}")


def save_resume(db_path: str, user_id: int, user_email: str, 
                filename: str, file_content: bytes) -> Optional[str]:
    """
    Save a user's uploaded resume file.
    
    Args:
        db_path: Path to SQLite database
        user_id: User ID
        user_email: User email
        filename: Original filename
        file_content: File content as bytes
    
    Returns:
        File path if successful, None otherwise
    """
    try:
        # Get resumes directory (absolute path)
        resumes_dir = get_resumes_dir()
        
        # Create user-specific directory
        user_dir = resumes_dir / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename with timestamp
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        safe_filename = "".join(c for c in filename if c.isalnum() or c in "._- ")
        file_path = user_dir / f"{timestamp}_{safe_filename}"
        
        # Save file
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # Save to database with absolute path
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        uploaded_at = datetime.now(timezone.utc).isoformat()
        
        # Store absolute path
        absolute_path = str(file_path.resolve())
        
        cursor.execute("""
            INSERT INTO resume_uploads 
            (user_id, user_email, filename, file_path, uploaded_at)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, user_email, filename, absolute_path, uploaded_at))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Resume saved for user {user_email}: {filename}")
        return str(file_path)
    
    except Exception as e:
        logger.error(f"Error saving resume: {e}")
        return None


def get_user_searches(db_path: str, user_id: Optional[int] = None) -> List[dict]:
    """
    Get search history for a user or all users.
    
    Args:
        db_path: Path to SQLite database
        user_id: Optional user ID to filter by
    
    Returns:
        List of search dictionaries
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        if user_id:
            cursor.execute("""
                SELECT id, user_id, user_email, role, time_window, location, 
                       remote_only, searched_at
                FROM search_history
                WHERE user_id = ?
                ORDER BY searched_at DESC
            """, (user_id,))
        else:
            cursor.execute("""
                SELECT id, user_id, user_email, role, time_window, location, 
                       remote_only, searched_at
                FROM search_history
                ORDER BY searched_at DESC
            """)
        
        rows = cursor.fetchall()
        conn.close()
        
        searches = []
        for row in rows:
            searches.append({
                'id': row[0],
                'user_id': row[1],
                'user_email': row[2],
                'role': row[3],
                'time_window': row[4],
                'location': row[5],
                'remote_only': bool(row[6]),
                'searched_at': row[7],
            })
        
        return searches
    
    except Exception as e:
        logger.error(f"Error getting user searches: {e}")
        return []


def get_user_resumes(db_path: str, user_id: Optional[int] = None) -> List[dict]:
    """
    Get resume uploads for a user or all users.
    
    Args:
        db_path: Path to SQLite database
        user_id: Optional user ID to filter by
    
    Returns:
        List of resume dictionaries
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        if user_id:
            cursor.execute("""
                SELECT id, user_id, user_email, filename, file_path, uploaded_at
                FROM resume_uploads
                WHERE user_id = ?
                ORDER BY uploaded_at DESC
            """, (user_id,))
        else:
            cursor.execute("""
                SELECT id, user_id, user_email, filename, file_path, uploaded_at
                FROM resume_uploads
                ORDER BY uploaded_at DESC
            """)
        
        rows = cursor.fetchall()
        conn.close()
        
        resumes = []
        for row in rows:
            resumes.append({
                'id': row[0],
                'user_id': row[1],
                'user_email': row[2],
                'filename': row[3],
                'file_path': row[4],
                'uploaded_at': row[5],
            })
        
        return resumes
    
    except Exception as e:
        logger.error(f"Error getting user resumes: {e}")
        return []
