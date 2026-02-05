import asyncio
from mavsdk import System

async def run():
    drone = System()
    address = "serial:///dev/tty.usbmodem101:115200"
    
    print(f"--- Connecting to Pixhawk on {address} ---")
    await drone.connect(system_address=address)

    async for state in drone.core.connection_state():
        if state.is_connected:
            print("--> Hardware Link: OK\n")
            break

    print("!!! PROPS MUST BE OFF - ENSURE BATTERY IS PLUGGED IN !!!")
    
    # We must be armed to spin motors
    print("Pressing Safety Switch now (if you have one)...")
    await asyncio.sleep(3) 

    try:
        print("Arming...")
        await drone.action.arm()
        
        # In ArduPilot, 'set_actuator' often expects values for the specific 
        # motor matrix. We'll try a small throttle blip.
        print("Spinning motors at 10% for 3 seconds...")
        
        # This sends a 'throttle' value to all motors simultaneously
        # to confirm they CAN spin.
        await drone.action.set_takeoff_altitude(2.0) # Dummy value to prime takeoff logic
        
        # We use manual control but ensure the throttle (3rd param) is high enough
        # format: (roll, pitch, throttle, yaw)
        for _ in range(30): # 3 seconds worth of pulses
            await drone.manual_control.set_manual_control_input(0.0, 0.0, 0.15, 0.0)
            await asyncio.sleep(0.1)

        await drone.action.disarm()
        print("Test Complete.")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    asyncio.run(run())
