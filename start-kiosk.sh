#!/bin/bash

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check and install dependencies
check_dependencies() {
    echo "Checking dependencies..."
    
    # List of required packages
    PACKAGES=(
        "chromium-browser"
        "unclutter"
        "x11-xserver-utils"
        "x11-utils"
        "python3"
        "python3-pip"
        "nodejs"
        "npm"
        "fuser"
    )
    
    MISSING_PACKAGES=()
    
    # Check each package
    for pkg in "${PACKAGES[@]}"; do
        if ! command_exists "$pkg"; then
            echo "Missing $pkg"
            MISSING_PACKAGES+=("$pkg")
        fi
    done
    
    # If there are missing packages, install them
    if [ ${#MISSING_PACKAGES[@]} -ne 0 ]; then
        echo "Installing missing packages..."
        sudo apt-get update
        sudo apt-get install -y "${MISSING_PACKAGES[@]}"
    fi
    
    # Check if python virtual environment exists
    if [ ! -d ".venv" ]; then
        echo "Setting up Python virtual environment..."
        python3 -m venv .venv
        source .venv/bin/activate
        pip install -r backend/requirements.txt
        deactivate
    fi
    
    # Check if node_modules exists
    if [ ! -d "frontend/node_modules" ]; then
        echo "Installing frontend dependencies..."
        cd frontend
        npm install
        cd ..
    fi
}

# Check and install dependencies
check_dependencies

# Export display if not set
export DISPLAY=:0
export XAUTHORITY=/home/$USER/.Xauthority

# Kill any processes running on ports 8000 and 5173
echo "Killing processes on ports 8000 and 5173..."
fuser -k 8000/tcp 2>/dev/null
fuser -k 5173/tcp 2>/dev/null

# Start the Python server
echo "Starting backend server..."
source .venv/bin/activate
cd backend
python3 main.py &
BACKEND_PID=$!

# Wait for backend to initialize
sleep 2

# Start the frontend dev server
echo "Starting frontend server..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

# Wait for frontend to initialize
sleep 2

# Kill any running Chromium processes
echo "Killing Chromium processes..."
pkill chromium-browser

# Hide the cursor using multiple methods
echo "Hiding cursor..."
if ! command -v unclutter >/dev/null 2>&1; then
    echo "unclutter not installed. Installing..."
    sudo apt-get update && sudo apt-get install -y unclutter
fi

# Kill any existing unclutter processes
pkill unclutter

# Start unclutter with more aggressive options
unclutter -idle 0 -root &

# Use X to hide cursor as backup method
xsetroot -cursor_name blank

# Create blank cursor
echo -e 'Xcursor.theme: default\nXcursor.size: 1' > ~/.Xresources
xrdb -merge ~/.Xresources

# Wait a moment for cursor hiding to take effect
sleep 2

# Launch Chromium in kiosk mode with additional flags
echo "Launching Chromium in kiosk mode..."
chromium-browser --kiosk \
    --disable-pinch \
    --overscroll-history-navigation=0 \
    --disable-features=TranslateUI \
    --noerrdialogs \
    --disable-infobars \
    --disable-gpu-compositing \
    --use-gl=egl \
    --enable-zero-copy \
    --no-sandbox \
    --ignore-certificate-errors \
    --test-type \
    --start-maximized \
    --force-device-scale-factor=1 \
    --touch-events=enabled \
    --ash-hide-cursor-when-typing \
    --password-store=basic \
    http://localhost:5173 2>/dev/null &

CHROMIUM_PID=$!

# Wait for all background processes
wait $BACKEND_PID $FRONTEND_PID $CHROMIUM_PID

# Cleanup function
cleanup() {
    echo "Cleaning up processes..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    kill $CHROMIUM_PID 2>/dev/null
    pkill chromium-browser
    pkill unclutter
    # Restore cursor
    xsetroot -cursor_name left_ptr
    deactivate 2>/dev/null
    exit 0
}

# Set up cleanup on script exit
trap cleanup SIGINT SIGTERM EXIT 