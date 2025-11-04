import os
from app import create_app, celery
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create Flask app for context
app = create_app(os.getenv('FLASK_ENV', 'development'))
app.app_context().push()

# Import tasks to register them with Celery
from app.tasks import generation_tasks

if __name__ == '__main__':
    # Start Celery worker
    celery.worker_main([
        'worker',
        '--loglevel=info',
        '--concurrency=2',  # Adjust based on your server capacity
        '--max-tasks-per-child=10'  # Restart workers after 10 tasks to prevent memory leaks
    ])