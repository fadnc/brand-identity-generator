import os
from app import create_app, db
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create Flask app
app = create_app(os.getenv('FLASK_ENV', 'development'))

# Create database tables
with app.app_context():
    db.create_all()
    print("Database tables created successfully!")

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'
    
    print(f"Starting Flask application on port {port}")
    print(f"Debug mode: {debug}")
    print(f"Environment: {os.getenv('FLASK_ENV', 'development')}")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )