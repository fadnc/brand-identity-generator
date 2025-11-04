import os
from flask_migrate import Migrate, init, migrate as migrate_db, upgrade
from app import create_app, db
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create app
app = create_app(os.getenv('FLASK_ENV', 'development'))

# Initialize Flask-Migrate
migrate = Migrate(app, db)

def initialize_migrations():
    """Initialize migration repository."""
    with app.app_context():
        try:
            init()
            print("✓ Migration repository initialized")
        except Exception as e:
            print(f"Migration repository already exists or error: {e}")

def create_migration(message="Auto migration"):
    """Create a new migration."""
    with app.app_context():
        try:
            migrate_db(message=message)
            print(f"✓ Migration created: {message}")
        except Exception as e:
            print(f"✗ Failed to create migration: {e}")

def apply_migrations():
    """Apply all pending migrations."""
    with app.app_context():
        try:
            upgrade()
            print("✓ All migrations applied successfully")
        except Exception as e:
            print(f"✗ Failed to apply migrations: {e}")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("""
Usage:
  python migrate.py init              - Initialize migrations
  python migrate.py create [message]  - Create new migration
  python migrate.py apply             - Apply migrations
        """)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'init':
        initialize_migrations()
    elif command == 'create':
        message = sys.argv[2] if len(sys.argv) > 2 else "Auto migration"
        create_migration(message)
    elif command == 'apply':
        apply_migrations()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)