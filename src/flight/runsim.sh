#!/bin/bash

# --- CONFIGURATION ---
ARDUPILOT_DIR="/Users/collin/drone/ardupilot"
ENV_PATH="/Users/collin/drone/env/droneEnv/bin/activate"

# --- COMMAND FOR WINDOW 1: The Drone & The Bridge ---
# 1. Build the code (just in case)
# 2. Run ArduCopter binary in BACKGROUND (bypassing the crashy launcher)
# 3. Run MAVProxy in FOREGROUND to bridge the connections
CMD_SITL="source $ENV_PATH; \
cd $ARDUPILOT_DIR; \
echo 'Building ArduCopter...'; \
./waf copter; \
echo 'Starting ArduCopter Binary (Manual Mode)...'; \
./build/sitl/bin/arducopter -S -I0 --model + --speedup 1 --defaults Tools/autotest/default_params/copter.parm > /tmp/arducopter.log 2>&1 & \
DRONE_PID=\$!; \
sleep 3; \
echo 'Drone is running (PID: \$DRONE_PID). Starting MAVProxy Bridge...'; \
mavproxy.py --master tcp:127.0.0.1:5760 --out udp:127.0.0.1:14540 --out udp:127.0.0.1:14550; \
kill \$DRONE_PID"

# --- COMMAND FOR WINDOW 2: MAVSDK Server ---
# Connects to the UDP port (14540) that MAVProxy in Window 1 creates
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
echo "1. Window 1 will show the MAVProxy Console (MAV>)."
echo "2. Window 2 will show MAVSDK waiting for connection."
echo "3. You can run your Python script here."
echo "--------------------------------------------------"
