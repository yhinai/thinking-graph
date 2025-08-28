#!/bin/bash

echo "Starting Application..."

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Set default ports if not found in .env
BACKEND_PORT=${BACKEND_PORT:-8000}
FRONTEND_PORT=${FRONTEND_PORT:-3000}

# Function to kill process on a specific port
kill_port() {
    local port=$1
    echo "Checking for processes on port $port..."
    
    # Find and kill process using the port
    local pid=$(lsof -ti:$port)
    if [ ! -z "$pid" ]; then
        echo "💀 Killing process $pid on port $port..."
        kill -9 $pid
        sleep 2
    else
        echo "Port $port is free"
    fi
}

# Function to check if a URL is accessible
check_url() {
    local url=$1
    local timeout=${2:-30}
    local attempts=0
    local max_attempts=$((timeout / 2))
    
    while [ $attempts -lt $max_attempts ]; do
        if curl -s -f "$url" >/dev/null 2>&1; then
            return 0
        fi
        attempts=$((attempts + 1))
        sleep 2
    done
    return 1
}

# Function to check backend health specifically
check_backend_health() {
    local url="http://localhost:$BACKEND_PORT/health"
    echo "Checking backend health..."
    
    if check_url "$url" 30; then
        local response=$(curl -s "$url" 2>/dev/null)
        if echo "$response" | grep -q '"status":"healthy"'; then
            echo "Backend is healthy and responding"
            return 0
        else
            echo "Backend responded but not healthy"
            return 1
        fi
    else
        echo "Backend health check failed"
        return 1
    fi
}

# Function to check frontend accessibility
check_frontend_health() {
    local url="http://localhost:$FRONTEND_PORT"
    echo "Checking frontend accessibility..."
    
    if check_url "$url" 30; then
        echo "Frontend is accessible"
        return 0
    else
        echo "Frontend accessibility check failed"
        return 1
    fi
}

# Kill processes on required ports
kill_port $FRONTEND_PORT
kill_port $BACKEND_PORT

echo ""
echo "Starting Backend Server (Port $BACKEND_PORT)..."

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Start backend server in background
cd "$SCRIPT_DIR/backend"
python app.py &
BACKEND_PID=$!

# Wait for backend to start
echo "Waiting for backend to start..."
sleep 5

# Check backend health
if ! check_backend_health; then
    echo "Backend failed to start properly"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo ""
echo "Starting Frontend Server (Port $FRONTEND_PORT)..."

# Start frontend server in background  
cd "$SCRIPT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!

# Wait for frontend to start
echo "Waiting for frontend to start..."
sleep 8

# Check frontend accessibility
if ! check_frontend_health; then
    echo "Frontend failed to start properly"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 1
fi

# Test API connectivity between frontend and backend
echo "Testing API connectivity..."
api_test=$(curl -s -X POST http://localhost:$BACKEND_PORT/api/chat \
    -H "Content-Type: application/json" \
    -d '{"message": "health check"}' \
    --max-time 10 2>/dev/null)

if echo "$api_test" | grep -q '"success"\|"response"'; then
    echo "API connectivity verified"
else
    echo "API connectivity test inconclusive (but servers are running)"
    echo "Response received: $api_test"
fi

echo ""
echo "Application Started Successfully!"
echo ""
echo "Access Points:"
echo "   Frontend: http://localhost:$FRONTEND_PORT"
echo "   Backend:  http://localhost:$BACKEND_PORT"
echo "   Health:   http://localhost:$BACKEND_PORT/health"
echo ""
echo "Process IDs:"
echo "   Backend PID:  $BACKEND_PID"
echo "   Frontend PID: $FRONTEND_PID"
echo ""
echo "To stop the application, run:"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo ""

# Function to cleanup on script exit
cleanup() {
    echo ""
    echo "Stopping Application..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    echo "Application stopped"
}

# Set up trap to cleanup on script exit
trap cleanup EXIT

# Keep script running and show logs
echo "Application is running. Press Ctrl+C to stop."
echo "Monitoring processes..."
echo ""

# Wait for processes to finish or until user interrupts
wait