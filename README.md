# 🎨 Brand Identity Generator

**An AI-powered SaaS platform for end-to-end brand creation using multi-agent systems and generative AI.**

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-green)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 📋 Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Usage Examples](#usage-examples)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

## ✨ Features

### Core Capabilities

- **🤖 Multi-Agent System**: Specialized agents for design, copywriting, and strategy
- **🎨 Logo Generation**: DALL-E 3 powered logo creation with style consistency
- **📝 Brand Copywriting**: Complete marketing copy, taglines, and brand stories
- **🎯 Strategic Positioning**: Competitive analysis and market positioning
- **🔄 A/B Testing**: Generate and compare multiple brand variants
- **✅ Consistency Checking**: Automated brand coherence validation
- **📊 Advanced Analytics**: Sentiment analysis, logo scoring, performance prediction
- **📦 Export Options**: PDF, ZIP, and JSON export formats
- **🔐 Secure Authentication**: JWT-based auth with role-based access

### Business Features

- **💰 Freemium Model**: Free, Premium, and Enterprise tiers
- **📈 Usage Tracking**: Monthly generation limits per tier
- **🎭 Brand Variants**: A/B testing with performance predictions
- **📉 Market Insights**: Trend analysis and competitive intelligence
- **🖼️ Visual Assets**: Logo, color palettes, typography recommendations
- **📱 Social Media Content**: Pre-generated posts and content templates

## 🏗️ Architecture

```
┌─────────────────┐
│   Next.js UI    │
│  (Frontend)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Flask API     │
│  (Backend)      │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌──────┐  ┌──────┐
│Redis │  │Celery│
│Queue │  │Worker│
└──────┘  └───┬──┘
              │
         ┌────┴────┐
         │         │
         ▼         ▼
    ┌────────┐ ┌────────┐
    │OpenAI  │ │ Agents │
    │API     │ │ System │
    └────────┘ └────────┘
         │         │
         └────┬────┘
              ▼
       ┌──────────┐
       │PostgreSQL│
       │ Database │
       └──────────┘
```

### Multi-Agent Workflow

```
User Request
    │
    ▼
┌─────────────────────┐
│  Brand Orchestrator │
└──────────┬──────────┘
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
┌─────────┐   ┌──────────┐   ┌──────────┐
│Strategy │   │ Design   │   │Copywrite │
│ Agent   │───│  Agent   │───│  Agent   │
└─────────┘   └──────────┘   └──────────┘
    │             │             │
    └─────────────┼─────────────┘
                  ▼
         ┌────────────────┐
         │  Consistency   │
         │    Checker     │
         └────────┬───────┘
                  │
                  ▼
           ┌──────────┐
           │  Final   │
           │  Output  │
           └──────────┘
```

## 🛠️ Tech Stack

### Backend
- **Framework**: Flask 3.0
- **Database**: PostgreSQL 13+
- **ORM**: SQLAlchemy
- **Task Queue**: Celery + Redis
- **Authentication**: Flask-JWT-Extended

### AI/ML
- **Language Models**: OpenAI GPT-4, GPT-3.5 Turbo
- **Image Generation**: DALL-E 3, Stable Diffusion
- **Orchestration**: LangChain, LangGraph
- **Vector DB**: Pinecone (optional)

### Infrastructure
- **Async Tasks**: Celery
- **Caching**: Redis
- **File Storage**: AWS S3 / Local
- **Monitoring**: Sentry (optional)

## 📥 Installation

### Prerequisites

- Python 3.9+
- PostgreSQL 13+
- Redis 6+
- OpenAI API Key

### Quick Start

```bash
# Clone repository
git clone https://github.com/yourusername/brand-identity-generator.git
cd brand-identity-generator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your credentials

# Initialize database
python migrate.py init
python migrate.py create "Initial migration"
python migrate.py apply

# Start services (3 terminals)

# Terminal 1: Flask
python run.py

# Terminal 2: Celery Worker
python celery_worker.py

# Terminal 3: Redis (if not running as service)
redis-server
```

See [SETUP.md](SETUP.md) for detailed installation instructions.

## 📚 API Documentation

### Base URL
```
http://localhost:5000/api
```

### Authentication Endpoints

#### Register User
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123",
  "full_name": "John Doe"
}
```

#### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123"
}
```

### Project Endpoints

#### Create Brand Project
```http
POST /api/projects/
Authorization: Bearer {token}
Content-Type: application/json

{
  "business_name": "TechStart Inc",
  "industry": "Technology",
  "target_audience": "Tech-savvy millennials",
  "brand_values": ["innovation", "reliability"],
  "competitors": ["CompetitorA", "CompetitorB"]
}
```

#### Get Project Status
```http
GET /api/generate/status/{project_id}
Authorization: Bearer {token}
```

#### Export Brand Package
```http
POST /api/generate/export/{project_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "format": "pdf",
  "include_assets": true,
  "include_guidelines": true
}
```

See full API documentation in [API.md](docs/API.md)

## 📁 Project Structure

```
brand-identity-generator/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── config.py                # Configuration
│   ├── models/                  # Database models
│   │   ├── user.py
│   │   ├── project.py
│   │   └── brand_assets.py
│   ├── agents/                  # Multi-agent system
│   │   ├── orchestrator.py      # Main coordinator
│   │   ├── design_agent.py      # Logo & visual
│   │   ├── copywriting_agent.py # Content creation
│   │   └── strategy_agent.py    # Brand strategy
│   ├── services/                # Business logic
│   │   ├── image_generation.py
│   │   ├── consistency_checker.py
│   │   └── export.py
│   ├── analytics/               # Analytics & ML
│   │   ├── sentiment_analysis.py
│   │   ├── logo_scorer.py
│   │   └── market_trends.py
│   ├── api/                     # API routes
│   │   ├── auth.py
│   │   ├── projects.py
│   │   ├── generation.py
│   │   └── analytics.py
│   ├── tasks/                   # Celery tasks
│   │   └── generation_tasks.py
│   └── utils/                   # Utilities
├── tests/                       # Test suite
│   ├── conftest.py
│   ├── test_auth.py
│   └── test_projects.py
├── migrations/                  # Database migrations
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
├── run.py                       # Application entry
├── celery_worker.py            # Celery worker
└── README.md                    # This file
```

## 💡 Usage Examples

### Python SDK Example

```python
import requests

# Base URL
BASE_URL = "http://localhost:5000/api"

# Register and login
register_response = requests.post(f"{BASE_URL}/auth/register", json={
    "email": "demo@example.com",
    "password": "DemoPass123",
    "full_name": "Demo User"
})

login_response = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "demo@example.com",
    "password": "DemoPass123"
})

token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Create brand project
project_response = requests.post(
    f"{BASE_URL}/projects/",
    headers=headers,
    json={
        "business_name": "EcoTech Solutions",
        "industry": "Sustainable Technology",
        "target_audience": "Environmentally conscious consumers",
        "brand_values": ["sustainability", "innovation", "transparency"],
        "competitors": ["GreenTech Inc", "EarthFirst"]
    }
)

project_id = project_response.json()["project"]["id"]
print(f"Project created: {project_id}")

# Check status (poll until complete)
import time
while True:
    status_response = requests.get(
        f"{BASE_URL}/generate/status/{project_id}",
        headers=headers
    )
    status = status_response.json()["status"]
    print(f"Status: {status}")
    
    if status == "completed":
        break
    elif status == "failed":
        print("Generation failed!")
        break
    
    time.sleep(10)

# Get complete project
project_detail = requests.get(
    f"{BASE_URL}/projects/{project_id}",
    headers=headers
)

brand_data = project_detail.json()["project"]
print(f"Brand created: {brand_data['business_name']}")
print(f"Consistency Score: {brand_data['consistency_score']}")

# Export as PDF
export_response = requests.post(
    f"{BASE_URL}/generate/export/{project_id}",
    headers=headers,
    json={"format": "pdf"}
)

print(f"Export ready: {export_response.json()['download_url']}")
```

### cURL Examples

```bash
# Register
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestPass123","full_name":"Test User"}'

# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestPass123"}'

# Create Project (replace TOKEN)
curl -X POST http://localhost:5000/api/projects/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"business_name":"MyBrand","industry":"Retail","target_audience":"Young adults","brand_values":["quality","affordability"]}'
```

## 🧪 Testing

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-asyncio

# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_auth.py

# Run with verbose output
pytest -v
```

## 🚀 Deployment

### Production Checklist

- [ ] Set `FLASK_ENV=production`
- [ ] Use strong `SECRET_KEY` and `JWT_SECRET_KEY`
- [ ] Configure production PostgreSQL
- [ ] Setup AWS S3 for file storage
- [ ] Configure Sentry for error tracking
- [ ] Setup SSL certificates
- [ ] Configure rate limiting
- [ ] Setup monitoring and logging
- [ ] Configure backup strategy
- [ ] Setup CI/CD pipeline

### Docker Deployment

```bash
# Build image
docker build -t brand-identity-generator .

# Run with docker-compose
docker-compose up -d
```

### Heroku Deployment

```bash
# Login and create app
heroku login
heroku create your-app-name

# Add buildpacks
heroku buildpacks:add heroku/python

# Set environment variables
heroku config:set OPENAI_API_KEY=your_key

# Deploy
git push heroku main

# Run migrations
heroku run python migrate.py apply
```

## 💰 Pricing Tiers

| Feature | Free | Premium | Enterprise |
|---------|------|---------|------------|
| Generations/month | 10 | 100 | 1000 |
| A/B Variants | 3 | 5 | Unlimited |
| Export Formats | JSON | All | All + API |
| Analytics | Basic | Advanced | Full |
| Support | Community | Email | Priority |

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

## 🙏 Acknowledgments

- OpenAI for GPT-4 and DALL-E 3
- LangChain for agent orchestration
- Flask community
- All contributors

## 📧 Contact

- **Email**: support@brandidentitygen.com
- **GitHub**: [@yourusername](https://github.com/yourusername)
- **Documentation**: [docs.brandidentitygen.com](https://docs.brandidentitygen.com)

---

**Built with ❤️ for the capstone project**

⭐ Star this repo if you find it helpful!