#!/bin/bash

# ============================================================================
# Brand Identity Generator - Automated Setup Script
# ============================================================================

set -e  # Exit on error

echo "========================================================================"
echo "  Brand Identity Generator - Automated Setup"
echo "========================================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check Python version
print_status "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then 
    print_success "Python $python_version detected ✓"
else
    print_error "Python 3.9+ required. Found: $python_version"
    exit 1
fi

# Ask for installation type
echo ""
echo "Select installation type:"
echo "  1) Minimal (Quick start, ~500MB)"
echo "  2) Full (All features, ~2.5GB)"
echo "  3) Production (Optimized, ~1GB)"
echo ""
read -p "Enter choice [1-3]: " install_choice

case $install_choice in
    1)
        requirements_file="requirements-minimal.txt"
        print_status "Installing minimal setup..."
        ;;
    2)
        requirements_file="requirements.txt"
        print_status "Installing full setup..."
        ;;
    3)
        requirements_file="requirements-production.txt"
        print_status "Installing production setup..."
        ;;
    *)
        print_error "Invalid choice"
        exit 1
        ;;
esac

# Create virtual environment
print_status "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_warning "Virtual environment already exists"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate
print_success "Virtual environment activated"

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
print_success "Pip upgraded"

# Install requirements
print_status "Installing Python packages (this may take several minutes)..."
pip install -r "$requirements_file"
print_success "Python packages installed"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    print_status "Creating .env file..."
    cp .env.example .env
    print_success ".env file created"
    print_warning "Please edit .env and add your API keys!"
else
    print_warning ".env file already exists"
fi

# Check for PostgreSQL
print_status "Checking PostgreSQL..."
if command -v psql &> /dev/null; then
    print_success "PostgreSQL found"
else
    print_warning "PostgreSQL not found. Please install it:"
    echo "  macOS:   brew install postgresql"
    echo "  Ubuntu:  sudo apt-get install postgresql"
    echo "  Windows: Download from postgresql.org"
fi

# Check for Redis
print_status "Checking Redis..."
if command -v redis-cli &> /dev/null; then
    print_success "Redis found"
else
    print_warning "Redis not found. Please install it:"
    echo "  macOS:   brew install redis"
    echo "  Ubuntu:  sudo apt-get install redis-server"
    echo "  Windows: Use WSL or download from redis.io"
fi

# Create necessary directories
print_status "Creating directories..."
mkdir -p app/static/uploads
mkdir -p app/static/exports
mkdir -p logs
print_success "Directories created"

# Initialize database migrations
print_status "Initializing database migrations..."
if [ ! -d "migrations" ]; then
    python migrate.py init
    print_success "Database migrations initialized"
else
    print_warning "Migrations directory already exists"
fi

# Summary
echo ""
echo "========================================================================"
echo "  Setup Complete!"
echo "========================================================================"
echo ""
echo "Next Steps:"
echo ""
echo "1. Configure environment variables:"
echo "   ${YELLOW}nano .env${NC}"
echo "   Add your OPENAI_API_KEY and database credentials"
echo ""
echo "2. Create PostgreSQL database:"
echo "   ${YELLOW}createdb brand_identity_dev${NC}"
echo ""
echo "3. Run database migrations:"
echo "   ${YELLOW}python migrate.py create 'Initial migration'${NC}"
echo "   ${YELLOW}python migrate.py apply${NC}"
echo ""
echo "4. Start the services (3 separate terminals):"
echo ""
echo "   Terminal 1 (Flask):"
echo "   ${YELLOW}source venv/bin/activate${NC}"
echo "   ${YELLOW}python run.py${NC}"
echo ""
echo "   Terminal 2 (Celery):"
echo "   ${YELLOW}source venv/bin/activate${NC}"
echo "   ${YELLOW}python celery_worker.py${NC}"
echo ""
echo "   Terminal 3 (Redis):"
echo "   ${YELLOW}redis-server${NC}"
echo ""
echo "5. Test the API:"
echo "   ${YELLOW}curl http://localhost:5000/health${NC}"
echo ""
echo "========================================================================"
echo "  Documentation: README.md"
echo "  API Docs: http://localhost:5000/api/docs (after starting)"
echo "========================================================================"
echo ""
print_success "Happy coding! 🚀"