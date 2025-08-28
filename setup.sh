#!/bin/bash

# Setup script for Thinking Graph application
# This script installs all required dependencies and sets up the environment

set -e  # Exit on any error

echo "🚀 Setting up Thinking Graph Application..."
echo "========================================"

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

# Check if running on macOS or Linux
if [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="macOS"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    PLATFORM="Linux"
else
    print_error "Unsupported operating system: $OSTYPE"
    exit 1
fi

print_status "Detected platform: $PLATFORM"

# Check for required system dependencies
print_status "Checking system dependencies..."

# Check for Node.js
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js from https://nodejs.org/"
    exit 1
fi
NODE_VERSION=$(node --version)
print_success "Node.js found: $NODE_VERSION"

# Check for npm
if ! command -v npm &> /dev/null; then
    print_error "npm is not installed. Please install npm."
    exit 1
fi
NPM_VERSION=$(npm --version)
print_success "npm found: v$NPM_VERSION"

# Check for Python3
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3."
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
print_success "Python 3 found: $PYTHON_VERSION"

# Check for pip3
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 is not installed. Please install pip3."
    exit 1
fi
PIP_VERSION=$(pip3 --version)
print_success "pip3 found: $PIP_VERSION"

# Install frontend dependencies
print_status "Installing frontend dependencies..."
cd frontend
if [ -f "package.json" ]; then
    npm install
    print_success "Frontend dependencies installed successfully"
else
    print_error "frontend/package.json not found!"
    exit 1
fi
cd ..

# Install backend dependencies
print_status "Installing backend dependencies..."
if [ -f "backend/requirements.txt" ]; then
    pip3 install -r backend/requirements.txt
    print_success "Backend dependencies installed successfully"
else
    print_error "backend/requirements.txt not found!"
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    print_status "Creating .env file..."
    cat > .env << EOL
# Environment Configuration
BACKEND_PORT=8000
FRONTEND_PORT=3000

# Neo4j Configuration (if using local Neo4j)
NEO4J_URI=neo4j://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# API Keys (add your keys here)
OPENAI_API_KEY=your_openai_key_here
GOOGLE_API_KEY=your_google_key_here

# Galileo Configuration
GALILEO_API_KEY=your_galileo_key_here
GALILEO_PROJECT_NAME=thinking-graph
EOL
    print_warning "Created .env file with default values. Please update with your actual API keys."
else
    print_status ".env file already exists"
fi

# Make scripts executable
print_status "Making scripts executable..."
chmod +x start.sh
chmod +x setup.sh
print_success "Scripts made executable"

# Create lib directory and files if they don't exist
print_status "Ensuring required frontend lib files exist..."
if [ ! -d "frontend/lib" ]; then
    mkdir -p frontend/lib
fi

if [ ! -f "frontend/lib/api.ts" ]; then
    print_warning "frontend/lib/api.ts not found - this should have been created during setup"
fi

if [ ! -f "frontend/lib/utils.ts" ]; then
    print_warning "frontend/lib/utils.ts not found - this should have been created during setup"
fi

# Test the setup
print_status "Testing setup..."
cd backend
if python3 -c "import flask, flask_cors, neo4j, openai, waitress; print('All backend imports successful')" 2>/dev/null; then
    print_success "Backend dependencies verified"
else
    print_error "Some backend dependencies are missing or broken"
    exit 1
fi
cd ..

# Check if Next.js can be found
cd frontend
if npx next --version &> /dev/null; then
    print_success "Frontend dependencies verified"
else
    print_error "Frontend dependencies are missing or broken"
    exit 1
fi
cd ..

echo ""
print_success "Setup completed successfully!"
echo ""
echo "🎉 Thinking Graph Application is ready to use!"
echo ""
echo "Next steps:"
echo "1. Update your .env file with actual API keys"
echo "2. Run './start.sh' to start the application"
echo "3. Access the frontend at http://localhost:3000"
echo "4. Access the backend API at http://localhost:8000"
echo ""
echo "For more information, see the README.md files in frontend/ and backend/ directories."