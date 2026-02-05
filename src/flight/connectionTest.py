import asyncio
from mavsdk import System

async def run():
    drone = System()
    
    # Common ports: /dev/ttyACM0 (Pi/Standard), /dev/ttyUSB0 (Jetson/Adapters)
    # command to find port on mac: (ls /dev/tty.usbmodem*) 
    ports_to_try = [
        "udp://:14540",
        "udp:127.0.0.1:14540",
        "serial:///dev/tty.usbmodem101:115200",
        "serial:///dev/ttyACM0:115200", 
        "serial:///dev/ttyACM1:115200",
        "serial:///dev/ttyUSB0:115200"
    ]

    connected = False
    for port in ports_to_try:
        print(f"Attempting to connect on {port}...")
        try:
            # We use a short timeout for the search
            await asyncio.wait_for(drone.connect(system_address=port), timeout=5)
            
            # Check if we actually see heartbeats
            async for state in drone.core.connection_state():
                if state.is_connected:
                    print(f"--> SUCCESS: Connected on {port}!")
                    connected = True
                    break
            if connected: break
        except Exception:
            print(f"No drone found on {port}")

    if not connected:
        print("FAILED: Could not find a flight controller. See checklist below.")
        return

    # Basic Health Check
    async for health in drone.telemetry.health():
        print(f"GPS Fix: {health.is_global_position_ok}")
        print(f"Armable: {health.is_armable}")
        break

if __name__ == "__main__":
    asyncio.run(run())
