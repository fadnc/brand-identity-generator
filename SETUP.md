# Brand Identity Generator - Setup Guide

## Prerequisites

- Python 3.9+
- PostgreSQL 13+
- Redis 6+
- OpenAI API Key
- (Optional) Pinecone API Key for vector storage

## Installation Steps

### 1. Clone and Setup Virtual Environment

```bash
# Create project directory
mkdir brand-identity-generator
cd brand-identity-generator

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Setup PostgreSQL Database

```bash
# Create database
createdb brand_identity_dev

# Or using psql:
psql -U postgres
CREATE DATABASE brand_identity_dev;
\q
```

### 4. Setup Redis

```bash
# Install Redis (Ubuntu/Debian)
sudo apt-get install redis-server

# Start Redis
sudo systemctl start redis-server

# Or on Mac with Homebrew:
brew install redis
brew services start redis
```

### 5. Configure Environment Variables

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your credentials
nano .env
```

**Required Configuration:**
- `OPENAI_API_KEY`: Your OpenAI API key
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: Generate a secure random key
- `JWT_SECRET_KEY`: Generate another secure key

```bash
# Generate secure keys
python -c "import secrets; print(secrets.token_hex(32))"
```

### 6. Initialize Database

```bash
# Initialize migrations
python migrate.py init

# Create initial migration
python migrate.py create "Initial migration"

# Apply migrations
python migrate.py apply

# Or simply run to create tables
python run.py
```

### 7. Start Services

You'll need **three terminal windows**:

**Terminal 1 - Flask Application:**
```bash
python run.py
```

**Terminal 2 - Celery Worker:**
```bash
python celery_worker.py
```

**Terminal 3 - Redis (if not running as service):**
```bash
redis-server
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login
- `POST /api/auth/refresh` - Refresh token
- `GET /api/auth/me` - Get current user
- `PUT /api/auth/me` - Update profile
- `POST /api/auth/change-password` - Change password
- `POST /api/auth/upgrade` - Upgrade tier

### Projects
- `GET /api/projects/` - List projects
- `POST /api/projects/` - Create project (start generation)
- `GET /api/projects/<id>` - Get project details
- `PUT /api/projects/<id>` - Update project
- `DELETE /api/projects/<id>` - Delete project
- `POST /api/projects/<id>/regenerate` - Regenerate brand
- `POST /api/projects/<id>/variants` - Generate variants

### Generation
- `GET /api/generate/status/<id>` - Check generation status
- `POST /api/generate/export/<id>` - Export brand package
- `POST /api/generate/logo/<id>/variations` - Generate logo variations
- `POST /api/generate/tagline/<id>/alternatives` - Generate taglines
- `POST /api/generate/refine/<id>` - Refine brand identity
- `GET /api/generate/preview/<id>` - Preview mockups

### Analytics
- `GET /api/analytics/sentiment/<id>` - Sentiment analysis
- `GET /api/analytics/logo-score/<id>` - Score logo quality
- `POST /api/analytics/market-trends` - Market trend analysis
- `GET /api/analytics/compare-variants/<id>` - Compare variants
- `GET /api/analytics/consistency-report/<id>` - Consistency report
- `GET /api/analytics/competitive-positioning/<id>` - Competitive analysis
- `GET /api/analytics/performance-prediction/<id>` - Predict performance

## Testing the API

### 1. Register a User

```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123",
    "full_name": "Test User"
  }'
```

### 2. Create a Brand Project

```bash
curl -X POST http://localhost:5000/api/projects/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "business_name": "TechStart Inc",
    "industry": "Technology",
    "target_audience": "Tech-savvy millennials and Gen Z",
    "brand_values": ["innovation", "reliability", "sustainability"],
    "competitors": ["CompetitorA", "CompetitorB"]
  }'
```

### 3. Check Generation Status

```bash
curl http://localhost:5000/api/generate/status/1 \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Production Deployment

### Environment Setup

1. **Set Production Environment:**
```bash
export FLASK_ENV=production
```

2. **Use Production Database:**
```bash
export DATABASE_URL=postgresql://user:password@prod-host/brand_identity_prod
```

3. **Configure AWS S3 for Asset Storage:**
```bash
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export S3_BUCKET_NAME=your_bucket
```

### Gunicorn Setup

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

### Supervisor Configuration (for Celery)

Create `/etc/supervisor/conf.d/celery.conf`:

```ini
[program:celery]
command=/path/to/venv/bin/python /path/to/celery_worker.py
directory=/path/to/project
user=www-data
numprocs=1
stdout_logfile=/var/log/celery/worker.log
stderr_logfile=/var/log/celery/worker.log
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=600
```

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static {
        alias /path/to/project/app/static;
    }
}
```

## Monitoring

### Setup Sentry (Error Tracking)

```bash
# Add to .env
SENTRY_DSN=your_sentry_dsn
```

### Log Files

- Flask logs: Check console output or configure file logging
- Celery logs: `/var/log/celery/worker.log`
- Nginx logs: `/var/log/nginx/access.log` and `error.log`

## Troubleshooting

### Database Connection Issues

```bash
# Test PostgreSQL connection
psql -U postgres -d brand_identity_dev

# Check if database exists
\l
```

### Redis Connection Issues

```bash
# Test Redis
redis-cli ping
# Should return: PONG
```

### Celery Task Issues

```bash
# Check Celery task queue
celery -A app.celery inspect active

# Purge all tasks
celery -A app.celery purge
```

### OpenAI API Issues

- Verify API key is correct
- Check API usage limits
- Monitor rate limits

## Cost Optimization Tips

1. **Use GPT-3.5 Turbo for non-critical tasks**
2. **Implement caching for similar requests**
3. **Set rate limits per user tier**
4. **Use Stable Diffusion as DALL-E alternative**
5. **Batch similar requests**

## Development Tips

1. **Use pytest for testing:**
```bash
pytest tests/
```

2. **Run code quality checks:**
```bash
flake8 app/
black app/
```

3. **Monitor API costs:**
```bash
# Add logging for OpenAI API calls
# Track usage in database
```

## Support

For issues or questions:
1. Check logs first
2. Review API documentation
3. Test with Postman/curl
4. Check OpenAI API status

## Next Steps

1. ✅ Complete basic setup
2. ✅ Test API endpoints
3. 🔄 Build frontend (Next.js)
4. 🔄 Add payment integration (Stripe)
5. 🔄 Implement monitoring
6. 🔄 Deploy to production