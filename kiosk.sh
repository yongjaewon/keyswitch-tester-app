#!/bin/bash

# Set up display environment
export DISPLAY=:0
export XAUTHORITY=/home/$USER/.Xauthority

# Function to get display information
get_dsi_display() {
    echo "Using Screen 0..."
    DSI_DISPLAY="0"
    
    # Get resolution
    RESOLUTION=$(xrandr | grep "Screen 0" | grep -o "current [0-9]* x [0-9]*" | awk '{print $2 "x" $4}')
    if [ -z "$RESOLUTION" ]; then
        echo "Could not detect resolution, using default 1920x1080"
        RESOLUTION="1920x1080"
    fi
    WIDTH=$(echo $RESOLUTION | cut -d"x" -f1)
    HEIGHT=$(echo $RESOLUTION | cut -d"x" -f2)
    echo "Display resolution: ${WIDTH}x${HEIGHT}"
}

# Function to check if site is accessible
check_site() {
    echo "Checking if site is accessible..."
    for i in {1..30}; do
        if curl -k -s -o /dev/null https://eminently-bold-cougar.ngrok-free.app; then
            echo "Site is accessible!"
            return 0
        fi
        echo "Waiting for site to become accessible... (attempt $i/30)"
        sleep 1
    done
    echo "Site is not accessible after 30 seconds"
    return 1
}

# Get DSI display information
get_dsi_display

# Kill any running Chromium processes
echo "Killing Chromium processes..."
pkill -f chromium-browser

# Kill any existing unclutter processes
pkill unclutter

# Hide the cursor using multiple methods
echo "Hiding cursor..."

# Start unclutter with more aggressive options
unclutter -idle 0 -root &

# Use X to hide cursor as backup method
xsetroot -cursor_name blank

# Create blank cursor
echo -e 'Xcursor.theme: default\nXcursor.size: 1' > ~/.Xresources
xrdb -merge ~/.Xresources

# Wait a moment for cursor hiding to take effect
sleep 2

# Check if site is accessible
if ! check_site; then
    echo "Error: Cannot access the site. Please check if launch.sh is running."
    cleanup
    exit 1
fi

# Launch Chromium in kiosk mode
echo "Starting kiosk display on Screen 0..."
chromium-browser \
    --kiosk \
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
    --window-position=0,0 \
    --window-size=$WIDTH,$HEIGHT \
    --user-data-dir=/tmp/chrome \
    --disable-web-security \
    --allow-running-insecure-content \
    --disable-site-isolation-trials \
    --display=:0 \
    http://localhost:3000 2>/dev/null &

CHROME_PID=$!
echo "Chrome process started with PID: $CHROME_PID"

# Wait for Chrome to start and load
echo "Waiting for Chrome to initialize..."
sleep 15

# Check if Chrome is still running
if ! ps -p $CHROME_PID > /dev/null; then
    echo "Error: Chrome process died. Check if it's installed and working properly."
    cleanup
    exit 1
fi

# Use xdotool to ensure window is focused and fullscreen
if command -v xdotool >/dev/null; then
    echo "Looking for Chrome window..."
    # Try multiple times to find the window
    for i in {1..10}; do
        echo "Attempt $i: Listing all windows..."
        xwininfo -root -tree
        
        for pattern in "chromium-browser" "Chromium" "chromium" "Chrome" "Navigator" "Browser"; do
            echo "Searching for window with pattern: $pattern"
            WID=$(xdotool search --onlyvisible --class "$pattern" 2>/dev/null | head -n 1)
            if [ -z "$WID" ]; then
                WID=$(xdotool search --onlyvisible --name "$pattern" 2>/dev/null | head -n 1)
            fi
            
            if [ ! -z "$WID" ]; then
                echo "Found window with ID: $WID using pattern: $pattern"
                echo "Activating window..."
                xdotool windowactivate --sync $WID
                echo "Moving window..."
                xdotool windowmove $WID 0 0
                echo "Setting window size..."
                xdotool windowsize $WID $WIDTH $HEIGHT
                echo "Window manipulation complete"
                break 2
            fi
        done
        
        if [ $i -eq 10 ]; then
            echo "Failed to find Chrome window after 10 attempts"
            echo "Current running processes:"
            ps aux | grep -i chrom
        else
            echo "Window not found, waiting before next attempt..."
            sleep 3
        fi
    done
else
    echo "xdotool not found, cannot manipulate window"
fi

# Cleanup function
cleanup() {
    echo "Cleaning up..."
    pkill -f chromium-browser
    pkill unclutter
    # Restore cursor
    xsetroot -cursor_name left_ptr
    # Clean up Chrome temporary data
    rm -rf /tmp/chrome
    exit 0
}

# Set up cleanup on script exit
trap cleanup SIGINT SIGTERM EXIT

# Keep script running
wait 