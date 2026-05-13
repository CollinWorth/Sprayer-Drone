"""
Spray test for OUTDOOR use — arms the drone via MAVSDK then fires actuator set 1.

Requirements:
  - GPS lock (or set COM_ARM_WO_GPS=1 in QGC to skip)
  - RC transmitter bound, or COM_ARM_WITHOUT_RC=1
  - Battery connected
  - CONNECTION_STRING set in src/flight/.env

Actuator mapping:
  - MAIN6 = "Peripheral via Actuator Set 1" in QGC Actuators
  - set_actuator(index=1, value=1.0)  => full on
  - set_actuator(index=1, value=-1.0) => off (normalized scale)

Run from repo root:
  python src/flight/testSprayArmed.py
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from drone_actions import Drone

SPRAY_DURATION = 2.0
ACTUATOR_INDEX = 1   # "Actuator Set 1" = index 1 in MAVSDK set_actuator()


async def spray(drone: Drone):
    print(f"SPRAY ON ({SPRAY_DURATION}s)...")
    await drone.system.actuator.set_actuator(ACTUATOR_INDEX, 1.0)
    await asyncio.sleep(SPRAY_DURATION)
    await drone.system.actuator.set_actuator(ACTUATOR_INDEX, -1.0)
    print("SPRAY OFF")


async def wait_for_space():
    """Async-friendly: run blocking stdin read in executor."""
    loop = asyncio.get_event_loop()
    print("Press SPACE + Enter to spray, Q + Enter to quit: ", end="", flush=True)
    ch = await loop.run_in_executor(None, lambda: sys.stdin.readline().strip().lower())
    return ch


async def main():
    drone = Drone()
    await drone.connect()

    print("Waiting for readiness (no GPS required)...")
    await drone.wait_for_readiness(require_gps=False)

    print("\n*** REMOVE PROPELLERS before arming indoors ***")
    confirm = input("Type YES to arm: ").strip()
    if confirm != "YES":
        print("Aborted.")
        return

    await drone.arm()
    print("--> Armed. Ready to spray.\n")

    try:
        while True:
            ch = await wait_for_space()
            if ch in ("q", "quit", "exit"):
                break
            if ch in ("", " ", "s", "spray"):
                await spray(drone)
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass

    print("Disarming...")
    await drone.disarm()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
