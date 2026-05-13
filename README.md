# Sprayer-Drone

Autonomous agricultural spray drone built on PX4, MAVSDK, and QGroundControl. The system flies a pre-planned route over a field and triggers the spray system at target zones. Built as a capstone project at the University of Idaho using off-the-shelf components and open source software.

## Hardware

- **Flight controller:** Cube Orange running PX4
- **Companion computer:** Raspberry Pi
- **Spray actuator:** Pump wired to MAIN6 output (Actuator Set 1 in QGC)
- **Ground station:** Laptop running QGroundControl

## Software Stack

| Tool | Role |
|------|------|
| PX4 | Flight control firmware on the Cube Orange |
| MAVSDK | Python SDK for programmatic flight commands |
| MAVLink | Communication protocol between Pi and flight controller |
| QGroundControl | Mission planning and ground station monitoring |

## Setup

**1. Install dependencies:**
```bash
pip install -r requirements.txt
```

**2. Configure `src/flight/.env`:**
```
# macOS
CONNECTION_STRING=serial:///dev/tty.usbmodem01:57600

# Linux (Raspberry Pi)
CONNECTION_STRING=serial:///dev/ttyACM0:57600

MISSION_PATH=/path/to/Sprayer-Drone/missions
MISSION_FILE=full_flight_day1.plan
```

If you're not sure which port the Cube Orange is on, run `connectionTest.py` to auto-discover it.

**3. Create a mission in QGroundControl** and save the `.plan` file to `missions/`.

## Running a Mission

```bash
cd src/flight
python3 smart_sprayer.py                     # uses MISSION_FILE from .env
python3 smart_sprayer.py my_field.plan       # override mission file
```

The script connects to the drone, uploads the mission, arms, launches, and monitors progress. When the final waypoint is reached it commands RTL. If RC input is detected mid-mission, the loop pauses and waits for mission mode to resume.

## Directory Structure

```
Sprayer-Drone/
├── missions/                       # QGroundControl .plan mission files
├── requirements.txt
└── src/
    └── flight/
        ├── .env                    # Connection string and mission path config
        ├── drone_actions.py        # Drone class wrapping MAVSDK System
        ├── smart_sprayer.py        # Main mission execution entry point
        ├── automationScripts/      # Simulation launch scripts
        │   ├── runsim.sh               # Start ArduCopter SITL + MAVProxy + MAVSDK
        │   ├── runsimParker.sh         # runsim.sh preset for Parker Farm
        │   └── cleanup.sh              # Kill all sim processes
        └── tests/                  # Diagnostic and test scripts
            ├── check_mission.py        # Validate .plan file (no drone needed)
            ├── check_all_missions.sh   # Batch validate all missions in missions/
            ├── check_gps.py            # Print GPS fix status and health flags
            ├── connectionTest.py       # Auto-discover flight controller port
            ├── testLaunch.py           # Takeoff, hover, land test
            ├── testSprayArmed.py       # Fire spray actuator (outdoor, arms drone)
            ├── testSpray.py            # Fire spray via QGC GUI slider (bench only)
            ├── testSprayNoArm.py       # Low-level pymavlink spray debug
            ├── propTest.py             # Arm motors and log status messages
            ├── flightTest2runner.py    # Run a hardcoded 3-waypoint mission
            └── test_upload.py          # Upload and verify a mission file
```

## Test Scripts

Run all test scripts from `src/flight/tests/`.

| Script | Drone needed | Arms | Purpose |
|--------|-------------|------|---------|
| `check_mission.py` | No | No | Validate .plan file coordinates |
| `check_all_missions.sh` | No | No | Batch validate all missions |
| `check_gps.py` | Yes | No | Check GPS fix and armability |
| `connectionTest.py` | Yes | No | Find and verify drone connection |
| `testLaunch.py` | Yes | Yes | Takeoff, hover, land |
| `testSprayArmed.py` | Yes | Yes | Spray actuator test (outdoor) |
| `testSpray.py` | No | No | Spray test via QGC slider GUI (bench) |
| `testSprayNoArm.py` | Yes | No | Low-level actuator debug via pymavlink |
| `propTest.py` | Yes | Yes | Arm/disarm and capture status errors |
| `flightTest2runner.py` | Yes | Yes | Fly hardcoded 3-waypoint test mission |
| `test_upload.py` | Yes | No | Upload mission and verify download |

**`testLaunch.py` usage:**
```bash
python3 testLaunch.py 10 5    # 10m altitude, 5s hover
```

## Simulation

`automationScripts/` contains scripts for running the drone in software simulation before flying.

```bash
cd src/flight/automationScripts

./runsim.sh                              # default simulator location
./runsim.sh lat,lon                      # custom location (e.g. 46.72,-116.95)
./runsim.sh lat,lon,alt,hdg             # full custom location

./runsimParker.sh                        # shortcut for Parker Farm coordinates
./cleanup.sh                             # kill all sim processes
```

`runsim.sh` opens two terminal windows: one running ArduCopter SITL + MAVProxy, one running the MAVSDK server. Once running, point QGroundControl at UDP port 14550 and run any of the flight scripts normally.

## Vision Integration

`smart_sprayer.py` includes a hook at the bottom of the mission loop for integrating the computer vision system. When a stress zone is detected, the intended flow is:

```python
await drone.action.hold()       # pause mission
# fire spray actuator
await drone.mission.start_mission()  # resume
```

The placeholder is at line ~128 in `smart_sprayer.py`.

## Notes

- `drone_actions.py` provides a `Drone` wrapper used by most test scripts. `smart_sprayer.py` uses MAVSDK's `System` directly to use the `mission_raw` API, which is required for importing QGC `.plan` files.
- `testSprayNoArm.py` uses raw pymavlink instead of MAVSDK. Bench testing indoors is unreliable — QGC's actuator slider is the only confirmed working path without flying.
- `testSpray.py` automates mouse clicks on QGC's actuator slider UI and requires no drone connection. Position the QGC window before running.
