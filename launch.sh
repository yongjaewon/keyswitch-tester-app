#!/bin/bash

# Function to check if a port is in use
check_port() {
    lsof -i ":$1" > /dev/null 2>&1
    return $?
}

# Function to kill process on a port
kill_port() {
    lsof -ti ":$1" | xargs kill -9 2>/dev/null
}

# Function to check if a port is available
check_port_available() {
    local port=$1
    timeout 1 bash -c "echo >/dev/tcp/localhost/$port" 2>/dev/null
    return $?
}

# Wait for port to be available
wait_for_port() {
    local port=$1
    local service=$2
    echo "Waiting for $service to be ready..."
    while check_port_available $port; do
        sleep 1
    done
}

echo "Starting services..."

# Kill any existing processes on our ports
echo "Cleaning up existing processes..."
kill_port 8000  # Backend
kill_port 3000  # Proxy
pkill ngrok     # Ngrok

# Wait for ports to be freed
sleep 2

# Start backend server
echo "Starting backend server..."
cd backend
python3 main.py &
BACKEND_PID=$!

# Wait for backend to be ready
wait_for_port 8000 "backend"

# Start proxy server
echo "Starting proxy server..."
cd ../frontend
node proxy-server.cjs &
PROXY_PID=$!

# Wait for proxy to be ready
wait_for_port 3000 "proxy"

# Start ngrok with static domain
echo "Starting ngrok tunnel..."
ngrok http --domain=eminently-bold-cougar.ngrok-free.app 3000 &
NGROK_PID=$!

# Function to handle script termination
cleanup() {
    echo "Stopping services..."
    kill $BACKEND_PID 2>/dev/null
    kill $PROXY_PID 2>/dev/null
    kill $NGROK_PID 2>/dev/null
    pkill ngrok
    exit
}

# Set up trap for cleanup on script termination
trap cleanup SIGINT SIGTERM

echo "All services started!"
echo "Backend running on http://localhost:8000"
echo "Proxy running on http://localhost:3000"
echo "Ngrok tunnel running on https://eminently-bold-cougar.ngrok-free.app"
echo "Press Ctrl+C to stop all services"

# Keep script running
wait 