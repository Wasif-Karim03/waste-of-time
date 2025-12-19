"""Script to create an admin user account."""

from app.storage.user_store import create_user, init_user_db
import sqlite3

# Admin credentials
ADMIN_EMAIL = "admin@jobpulse.com"
ADMIN_PASSWORD = "admin123"
ADMIN_NAME = "Administrator"

def create_admin_account():
    """Create admin account and set admin flag."""
    db_path = "./users.db"
    
    # Initialize database
    init_user_db(db_path)
    
    # Create admin user
    success, message = create_user(db_path, ADMIN_EMAIL, ADMIN_PASSWORD, ADMIN_NAME)
    
    if success:
        # Set is_admin flag
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE users
            SET is_admin = 1
            WHERE email = ?
        """, (ADMIN_EMAIL,))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Admin account created successfully!")
        print(f"   Email: {ADMIN_EMAIL}")
        print(f"   Password: {ADMIN_PASSWORD}")
        print(f"\n⚠️  IMPORTANT: Change the password after first login!")
    else:
        # User might already exist, just set admin flag
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE users
            SET is_admin = 1
            WHERE email = ?
        """, (ADMIN_EMAIL,))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Admin flag set for existing user!")
        print(f"   Email: {ADMIN_EMAIL}")
        print(f"   If password is unknown, you can reset it manually in the database.")

if __name__ == "__main__":
    create_admin_account()

