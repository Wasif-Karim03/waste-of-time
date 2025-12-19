"""Script to create test users for the application."""

from app.storage.user_store import create_user, init_user_db

# Test user data - 37 users
TEST_USERS = [
    {"name": "John Smith", "email": "john.smith@test.com", "password": "test123"},
    {"name": "Sarah Johnson", "email": "sarah.johnson@test.com", "password": "test123"},
    {"name": "Michael Brown", "email": "michael.brown@test.com", "password": "test123"},
    {"name": "Emily Davis", "email": "emily.davis@test.com", "password": "test123"},
    {"name": "David Wilson", "email": "david.wilson@test.com", "password": "test123"},
    {"name": "Jessica Martinez", "email": "jessica.martinez@test.com", "password": "test123"},
    {"name": "Christopher Anderson", "email": "christopher.anderson@test.com", "password": "test123"},
    {"name": "Amanda Taylor", "email": "amanda.taylor@test.com", "password": "test123"},
    {"name": "Matthew Thomas", "email": "matthew.thomas@test.com", "password": "test123"},
    {"name": "Ashley Jackson", "email": "ashley.jackson@test.com", "password": "test123"},
    {"name": "Daniel White", "email": "daniel.white@test.com", "password": "test123"},
    {"name": "Melissa Harris", "email": "melissa.harris@test.com", "password": "test123"},
    {"name": "James Martin", "email": "james.martin@test.com", "password": "test123"},
    {"name": "Michelle Thompson", "email": "michelle.thompson@test.com", "password": "test123"},
    {"name": "Robert Garcia", "email": "robert.garcia@test.com", "password": "test123"},
    {"name": "Laura Martinez", "email": "laura.martinez@test.com", "password": "test123"},
    {"name": "William Robinson", "email": "william.robinson@test.com", "password": "test123"},
    {"name": "Stephanie Clark", "email": "stephanie.clark@test.com", "password": "test123"},
    {"name": "Joseph Rodriguez", "email": "joseph.rodriguez@test.com", "password": "test123"},
    {"name": "Nicole Lewis", "email": "nicole.lewis@test.com", "password": "test123"},
    {"name": "Andrew Lee", "email": "andrew.lee@test.com", "password": "test123"},
    {"name": "Kimberly Walker", "email": "kimberly.walker@test.com", "password": "test123"},
    {"name": "Ryan Hall", "email": "ryan.hall@test.com", "password": "test123"},
    {"name": "Rebecca Allen", "email": "rebecca.allen@test.com", "password": "test123"},
    {"name": "Joshua Young", "email": "joshua.young@test.com", "password": "test123"},
    {"name": "Samantha King", "email": "samantha.king@test.com", "password": "test123"},
    {"name": "Kevin Wright", "email": "kevin.wright@test.com", "password": "test123"},
    {"name": "Rachel Lopez", "email": "rachel.lopez@test.com", "password": "test123"},
    {"name": "Brian Hill", "email": "brian.hill@test.com", "password": "test123"},
    {"name": "Lauren Scott", "email": "lauren.scott@test.com", "password": "test123"},
    {"name": "Justin Green", "email": "justin.green@test.com", "password": "test123"},
    {"name": "Megan Adams", "email": "megan.adams@test.com", "password": "test123"},
    {"name": "Brandon Baker", "email": "brandon.baker@test.com", "password": "test123"},
    {"name": "Brittany Nelson", "email": "brittany.nelson@test.com", "password": "test123"},
    {"name": "Tyler Carter", "email": "tyler.carter@test.com", "password": "test123"},
    {"name": "Amber Mitchell", "email": "amber.mitchell@test.com", "password": "test123"},
    {"name": "Jacob Perez", "email": "jacob.perez@test.com", "password": "test123"},
]

def create_test_users():
    """Create test user accounts."""
    db_path = "./users.db"
    
    # Initialize database
    init_user_db(db_path)
    
    created_count = 0
    skipped_count = 0
    
    print(f"Creating {len(TEST_USERS)} test users...\n")
    
    for user in TEST_USERS:
        success, message = create_user(
            db_path, 
            user["email"], 
            user["password"], 
            user["name"]
        )
        
        if success:
            created_count += 1
            print(f"✅ Created: {user['name']} ({user['email']})")
        else:
            skipped_count += 1
            print(f"⏭️  Skipped: {user['name']} ({user['email']}) - {message}")
    
    print(f"\n{'='*50}")
    print(f"Summary:")
    print(f"  ✅ Created: {created_count} users")
    print(f"  ⏭️  Skipped: {skipped_count} users (already exist)")
    print(f"{'='*50}")
    print(f"\nAll test users use password: test123")

if __name__ == "__main__":
    create_test_users()
