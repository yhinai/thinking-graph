#!/bin/bash

echo "Starting Application..."

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
    local url="http://localhost:8000/health"
    echo "Checking backend health..."
    
    if check_url "$url" 30; then
        local response=$(curl -s "$url" 2>/dev/null)
        if echo "$response" | grep -q '"status": "healthy"'; then
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
    local url="http://localhost:3000"
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
kill_port 3000
kill_port 8000

echo ""
echo "🔧 Starting Backend Server (Port 8000)..."

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
echo "🌐 Starting Frontend Server (Port 3000)..."

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
api_test=$(curl -s -X POST http://localhost:8000/api/chat \
    -H "Content-Type: application/json" \
    -d '{"message": "health check"}' \
    --max-time 10 2>/dev/null)

if echo "$api_test" | grep -q '"success"'; then
    echo "API connectivity verified"
else
    echo "API connectivity test inconclusive (but servers are running)"
fi

echo ""
echo "Application Started Successfully!"
echo ""
echo "Access Points:"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000"
echo "   Health:   http://localhost:8000/health"
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