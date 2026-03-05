#!/bin/bash

# --- CONFIGURATION ---
ARDUPILOT_DIR="/Users/collin/drone/ardupilot"
ENV_PATH="/Users/collin/drone/env/droneEnv/bin/activate"

# --- LOCATION HANDLING ---
# This block builds the variable LOCATION_ARG.
# It will either be empty (default) or contain "--home lat,lon,alt,hdg"
if [ -n "$1" ]; then
    # Count commas to see if user gave 2 numbers (lat,lon) or 4 (lat,lon,alt,hdg)
    COMMA_COUNT=$(echo "$1" | tr -cd ',' | wc -c | xargs)

    if [ "$COMMA_COUNT" -eq 1 ]; then
        echo "Detected Lat/Lon only. Adding default Alt (0m) and Heading (0 deg)."
        LOCATION_ARG="--home $1,0,0"
    elif [ "$COMMA_COUNT" -eq 3 ]; then
        echo "Custom location with Altitude/Heading detected."
        LOCATION_ARG="--home $1"
    else
        echo "ERROR: Invalid location format. Use 'lat,lon' OR 'lat,lon,alt,hdg'"
        exit 1
    fi
else
    echo "No custom location provided. Using Simulator Default."
    LOCATION_ARG=""
fi

# --- COMMAND FOR WINDOW 1: The Drone & The Bridge ---
# NOTICE: We use $LOCATION_ARG directly. Do NOT type '--home' before it.
CMD_SITL="source $ENV_PATH; \
cd $ARDUPILOT_DIR; \
echo 'Building ArduCopter...'; \
./waf copter; \
echo 'Starting ArduCopter Binary...'; \
./build/sitl/bin/arducopter -S -I0 --model + --speedup 1 $LOCATION_ARG --defaults Tools/autotest/default_params/copter.parm > /tmp/arducopter.log 2>&1 & \
DRONE_PID=\$!; \
sleep 3; \
echo 'Drone is running (PID: \$DRONE_PID). Starting MAVProxy Bridge...'; \
mavproxy.py --master tcp:127.0.0.1:5760 --out udp:127.0.0.1:14540 --out udp:127.0.0.1:14550; \
kill \$DRONE_PID"

# --- COMMAND FOR WINDOW 2: MAVSDK Server ---
CMD_MAVSDK="source $ENV_PATH; \
echo 'Starting MAVSDK Server...'; \
mavsdk_server -p 50051 udpin://:14540; \
read -n 1"

echo "--------------------------------------------------"
echo "LAUNCHING MANUAL DRONE SYSTEM"
echo "--------------------------------------------------"

echo "Opening Window 1: ArduCopter + MAVProxy..."
osascript -e "tell application \"Terminal\" to do script \"$CMD_SITL\""

echo "Opening Window 2: MAVSDK Server..."
osascript -e "tell application \"Terminal\" to do script \"$CMD_MAVSDK\""

echo "--------------------------------------------------"
echo "SYSTEM LAUNCHED."
echo "--------------------------------------------------"
